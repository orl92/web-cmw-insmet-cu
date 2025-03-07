from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.forms.user.form import UserForm, UserUpdateForm
from accounts.models import Profile

from django.contrib.admin.models import ADDITION, CHANGE, DELETION

from common.utils import log_action

# Create your views here.


class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = User
    template_name = 'pages/accounts/users/users.html'
    permission_required = 'auth.view_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Usuarios'
        context['parent'] = 'accounts'
        context['segment'] = 'users'
        context['btn'] = ('Añadir Usuario')
        context['url_create'] = reverse_lazy('create_user')
        context['url_list'] = reverse_lazy('users')
        context['objects'] = User.objects.all()
        return context
    
class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = 'pages/accounts/users/user_create.html'
    permission_required = 'auth.add_user'  # Permiso requerido para añadir un usuario
    success_url = reverse_lazy('users')
    url_redirect = success_url

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = True
        user.save()
        profile = Profile.objects.get(user=user)  # Crear o asegurar que el perfil existe
        profile.save()
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=user,
            action_flag=ADDITION,
            message=f"Se creó un nuevo usuario {user.username}."
        )
        
        messages.success(self.request, 'El usuario ha sido creado con éxito.', extra_tags='success')
        return redirect('update_user', uuid=profile.uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Usuarios'
        context['parent'] = 'accounts'
        context['segment'] = 'users'
        context['url_list'] = self.success_url
        return context

class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'pages/accounts/users/user_update.html'
    permission_required = 'auth.change_user'
    success_url = reverse_lazy('users')
    url_redirect = success_url

    def get_object(self):
        uuid = self.kwargs.get('uuid')
        profile = get_object_or_404(Profile, uuid=uuid)
        return profile.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_object()
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se editó el perfil de {self.object.username}."
        )
        
        messages.success(self.request, 'El usuario ha sido actualizado con éxito.', extra_tags='warning')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Usuario'
        context['parent'] = 'accounts'
        context['segment'] = 'users'
        context['url_list'] = self.success_url
        return context

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

class UserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = User
    template_name = 'pages/accounts/users/user_delete.html'
    permission_required = 'auth.delete_user'
    success_url = reverse_lazy('users')
    url_redirect = success_url

    def get_object(self):
        uuid = self.kwargs.get('uuid')
        profile = get_object_or_404(Profile, uuid=uuid)
        return profile.user

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        if user.is_superuser and User.objects.filter(is_superuser=True).count() == 1:
            messages.error(request, f'No se puede eliminar el usuario {user.username} si es el único superusuario.')
            return redirect(self.success_url)
        else:
            # Registro de acción antes de eliminar
            log_action(
                user=self.request.user,
                obj=user,
                action_flag=DELETION,
                message=f"Se eliminó al usuario {user.username}."
            )
            
            user.delete()
            messages.success(request, f'Usuario {user.username} se ha eliminado correctamente.')
            return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Usuario'
        context['message'] = f'¿Estás seguro de que deseas eliminar al usuario {self.object.username}?'
        context['button_text'] = 'Eliminar'
        context['parent'] = 'accounts'
        context['segment'] = 'users'
        context['url_list'] = reverse_lazy('users')
        return context