from collections import OrderedDict

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.contrib.auth.models import Group, Permission
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View

from apps.core.utils import log_action
from apps.user_auth.forms.groups import GroupForm
from apps.user_auth.models import GroupProfile, PermissionProfile


def _get_grouped_permissions(group=None, permissions=None):
    excluded = getattr(settings, 'GROUP_PERMISSION_EXCLUDED_APPS', [])
    merge = getattr(settings, 'GROUP_PERMISSION_APP_MERGE', {})
    merge_models = getattr(settings, 'GROUP_PERMISSION_MODEL_MERGE', {})

    qs = (
        Permission.objects.filter(
            content_type__app_label__in=[
                cfg.label
                for cfg in apps.get_app_configs()
                if cfg.label not in excluded
                and not cfg.name.startswith('django.contrib.')
                and cfg.get_models()
            ]
        )
        .select_related('content_type')
        .order_by('content_type__app_label', 'content_type__model', 'codename')
    )

    grouped = OrderedDict()
    if group is not None:
        selected = set(group.permissions.all())
    elif permissions is not None:
        selected = set(permissions)
    else:
        selected = set()

    for perm in qs:
        raw_app_label = perm.content_type.app_label
        app_label = merge.get(raw_app_label, raw_app_label)

        if app_label not in grouped:
            try:
                verbose_name = apps.get_app_config(app_label).verbose_name
            except LookupError:
                verbose_name = raw_app_label.title()
            grouped[app_label] = {'verbose_name': verbose_name, 'models': OrderedDict()}

        try:
            model_class = perm.content_type.model_class()
            model_name = (
                model_class._meta.verbose_name
                if model_class
                else perm.content_type.model.replace('_', ' ').title()
            )
        except AttributeError:
            model_name = perm.content_type.model.replace('_', ' ').title()

        model_name = merge_models.get(model_name, model_name)

        codename = perm.codename.lower()
        if codename.startswith('view_'):
            perm_type = 'view'
        elif codename.startswith('add_'):
            perm_type = 'add'
        elif codename.startswith('change_'):
            perm_type = 'change'
        elif codename.startswith('delete_'):
            perm_type = 'delete'
        else:
            continue

        if model_name not in grouped[app_label]['models']:
            grouped[app_label]['models'][model_name] = {
                'view': None,
                'add': None,
                'change': None,
                'delete': None,
            }

        if perm_type in grouped[app_label]['models'][model_name]:
            grouped[app_label]['models'][model_name][perm_type] = {
                'perm': perm,
                'field_name': 'permissions',
                'field_id': f'perm_{perm.id}',
                'is_checked': perm in selected,
            }

    return grouped


class GroupListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/user_auth/groups/list.html'
    permission_required = 'auth.view_group'
    model = Group

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Grupos'
        context['parent'] = 'user_auth'
        context['segment'] = 'groups'
        context['btn'] = 'Añadir Grupo'
        context['url_create'] = reverse_lazy('user_auth:group_create')
        context['url_list'] = reverse_lazy('user_auth:groups_list')
        context['is_superuser'] = self.request.user.is_superuser
        context['objects'] = Group.objects.all()
        return context


class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'pages/user_auth/groups/create.html'
    permission_required = 'auth.add_group'
    success_url = reverse_lazy('user_auth:groups_list')
    url_redirect = success_url

    def form_valid(self, form):
        group = form.save()
        group_profile, created = GroupProfile.objects.get_or_create(group=group)

        log_action(
            user=self.request.user,
            obj=group,
            action_flag=ADDITION,
            message=f'Se creó un nuevo grupo {group.name}.',
        )

        messages.success(self.request, 'El grupo ha sido creado con éxito.', extra_tags='success')
        return redirect('user_auth:groups_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Grupo'
        context['parent'] = 'user_auth'
        context['segment'] = 'groups'
        context['url_list'] = self.success_url
        context['grouped_by_app'] = _get_grouped_permissions()
        context['permission_profiles'] = PermissionProfile.objects.all()
        return context


class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'pages/user_auth/groups/update.html'
    permission_required = 'auth.change_group'
    success_url = reverse_lazy('user_auth:groups_list')

    def get_object(self):
        uuid = self.kwargs.get('uuid')
        group_profile = get_object_or_404(GroupProfile, uuid=uuid)
        return group_profile.group

    def form_valid(self, form):
        response = super().form_valid(form)

        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f'Se actualizó el grupo {self.object.name}.',
        )

        messages.success(
            self.request, 'El grupo ha sido actualizado con éxito.', extra_tags='warning'
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Grupo'
        context['parent'] = 'user_auth'
        context['segment'] = 'groups'
        context['url_list'] = self.success_url
        group = self.get_object()
        context['grouped_by_app'] = _get_grouped_permissions(group=group)
        context['permission_profiles'] = PermissionProfile.objects.all()
        return context

    def test_func(self):
        group = self.get_object()
        if group.name == 'Clientes' and 'Clientes' in self.request.user.groups.values_list(
            'name', flat=True
        ):
            return False
        return self.request.user.is_superuser or self.request.user.has_perm('auth.change_group')


class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'auth.delete_group'

    def post(self, request, uuid):
        group_profile = get_object_or_404(GroupProfile, uuid=uuid)
        group = group_profile.group
        group_name = group.name

        log_action(
            user=request.user,
            obj=group,
            action_flag=DELETION,
            message=f'Se eliminó el grupo {group_name}.',
        )
        group.delete()
        messages.success(request, f'Grupo {group_name} se ha eliminado correctamente.')
        return redirect('user_auth:groups_list')
