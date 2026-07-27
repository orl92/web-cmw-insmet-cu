from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View

from apps.user_auth.forms.permission_profiles import PermissionProfileForm
from apps.user_auth.models import PermissionProfile
from apps.user_auth.views.groups import _get_grouped_permissions
from apps.core.utils import log_action


class PermissionProfileListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = PermissionProfile
    template_name = 'pages/user_auth/permission_profiles/list.html'
    permission_required = 'user_auth.view_permissionprofile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Perfiles de Permisos'
        context['parent'] = 'user_auth'
        context['segment'] = 'permission_profiles'
        context['btn'] = 'Añadir Perfil'
        context['url_create'] = reverse_lazy('user_auth:permission_profile_create')
        context['url_list'] = reverse_lazy('user_auth:permission_profiles_list')
        context['is_superuser'] = self.request.user.is_superuser
        context['objects'] = self.object_list
        return context


class PermissionProfileCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = PermissionProfile
    form_class = PermissionProfileForm
    template_name = 'pages/user_auth/permission_profiles/create.html'
    permission_required = 'user_auth.add_permissionprofile'
    success_url = reverse_lazy('user_auth:permission_profiles_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=f'Se creó el perfil de permisos {self.object.name}.')
        messages.success(self.request, 'Perfil de permisos creado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Perfil de Permisos'
        context['parent'] = 'user_auth'
        context['segment'] = 'permission_profiles'
        context['url_list'] = self.success_url
        context['grouped_by_app'] = _get_grouped_permissions()
        return context


class PermissionProfileUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = PermissionProfile
    form_class = PermissionProfileForm
    pk_url_kwarg = 'uuid'
    template_name = 'pages/user_auth/permission_profiles/update.html'
    permission_required = 'user_auth.change_permissionprofile'
    success_url = reverse_lazy('user_auth:permission_profiles_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f'Se actualizó el perfil de permisos {self.object.name}.')
        messages.success(self.request, 'Perfil de permisos actualizado con éxito.', extra_tags='warning')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Perfil de Permisos'
        context['parent'] = 'user_auth'
        context['segment'] = 'permission_profiles'
        context['url_list'] = self.success_url
        profile = self.get_object()
        context['grouped_by_app'] = _get_grouped_permissions(permissions=profile.permissions.all())
        return context


class PermissionProfileDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'user_auth.delete_permissionprofile'

    def post(self, request, uuid):
        profile = get_object_or_404(PermissionProfile, uuid=uuid)
        name = profile.name
        log_action(
            user=request.user,
            obj=profile,
            action_flag=DELETION,
            message=f'Se eliminó el perfil de permisos {name}.')
        profile.delete()
        messages.success(request, f'Perfil de permisos "{name}" eliminado correctamente.')
        return redirect('user_auth:permission_profiles_list')
