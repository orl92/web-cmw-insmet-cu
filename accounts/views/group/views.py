from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.forms.group.form import GroupForm
from accounts.models import GroupProfile

from django.contrib.admin.models import ADDITION, CHANGE, DELETION

from common.utils import log_action

# Create your views here.

class GroupListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/accounts/groups/groups.html'
    permission_required = 'auth.view_group'
    model = Group

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Grupos'
        context['parent'] = 'accounts'
        context['segment'] = 'groups'
        context['btn'] = ('Añadir Grupo')
        context['url_create'] = reverse_lazy('create_group')
        context['url_list'] = reverse_lazy('groups')
        context['objects'] = Group.objects.all()

        return context
    
class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'pages/accounts/groups/group_create.html'
    permission_required = 'auth.add_group'
    success_url = reverse_lazy('groups')
    url_redirect = success_url

    def form_valid(self, form):
        group = form.save()
        group_profile, created = GroupProfile.objects.get_or_create(group=group)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=group,
            action_flag=ADDITION,
            message=f"Se creó un nuevo grupo {group.name}."
        )
        
        messages.success(self.request, 'El grupo ha sido creado con éxito.', extra_tags='success')
        return redirect('groups')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Grupos'
        context['parent'] = 'accounts'
        context['segment'] = 'groups'
        context['url_list'] = self.success_url
        return context

class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'pages/accounts/groups/group_update.html'
    permission_required = 'auth.change_group'
    success_url = reverse_lazy('groups')

    def get_object(self):
        uuid = self.kwargs.get('uuid')
        group_profile = get_object_or_404(GroupProfile, uuid=uuid)
        return group_profile.group

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó el grupo {self.object.name}."
        )
        
        messages.success(self.request, 'El grupo ha sido actualizado con éxito.', extra_tags='warning')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Grupo'
        context['parent'] = 'accounts'
        context['segment'] = 'groups'
        context['url_list'] = self.success_url
        return context

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Group
    template_name = 'pages/accounts/groups/group_delete.html'
    permission_required = 'auth.delete_group'
    success_url = reverse_lazy('groups')

    def get_object(self):
        uuid = self.kwargs.get('uuid')
        group_profile = get_object_or_404(GroupProfile, uuid=uuid)
        return group_profile.group

    def post(self, request, *args, **kwargs):
        group = self.get_object()
        
        # Registro de acción antes de eliminar el grupo
        log_action(
            user=self.request.user,
            obj=group,
            action_flag=DELETION,
            message=f"Se eliminó el grupo {group.name}."
        )
        
        try:
            group.delete()
            messages.success(request, 'El grupo ha sido eliminado con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, str(e))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Grupo'
        context['parent'] = 'accounts'
        context['segment'] = 'groups'
        context['url_list'] = reverse_lazy('groups')
        return context
