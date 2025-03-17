from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from accounts.forms.password.forms import (AdminPasswordChangeForm,
                                           UserPasswordChangeForm)

from django.contrib.admin.models import CHANGE
from common.utils import log_action


# Create your views here.

class PasswordChangeView(LoginRequiredMixin, FormView):
    template_name = 'pages/accounts/password/password_change.html'
    form_class = UserPasswordChangeForm
    success_url = reverse_lazy('profile')
    url_redirect = success_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # Pasar el usuario autenticado al formulario
        return kwargs

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)  # Mantener la sesión del usuario después de cambiar la contraseña
        
        # Registro de la acción
        log_action(
            user=self.request.user,
            obj=user,
            action_flag=CHANGE,
            message="El usuario cambió su contraseña."
        )
        
        messages.success(self.request, 'Tu contraseña ha sido cambiada con éxito.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs): 
        context = super().get_context_data(**kwargs) 
        context['title'] = 'Cambiar Contraseña' 
        context['parent'] = 'accounts' 
        context['segment'] = 'password_change' 
        context['url_list'] = self.success_url
        return context

class AdminPasswordChangeView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = 'pages/accounts/password/admin_password_change.html'
    form_class = AdminPasswordChangeForm
    permission_required = 'auth.change_user'
    success_url = reverse_lazy('users')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = get_object_or_404(User, profile__uuid=self.kwargs.get('uuid'))
        kwargs['instance'] = user  # Pasar el usuario a editar al formulario
        return kwargs

    def form_valid(self, form):
        user = form.save()
        
        # Registro de la acción
        log_action(
            user=self.request.user,
            obj=user,
            action_flag=CHANGE,
            message=f"El administrador {self.request.user.username} cambió la contraseña del usuario {user.username}."
        )
        
        messages.success(self.request, 'La contraseña del usuario ha sido cambiada con éxito.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Cambiar Contraseña del Usuario'
        context['parent'] = 'accounts'
        context['segment'] = 'password_change'
        context['url_list'] = self.success_url
        return context

class UserPasswordResetView(PasswordResetView):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request  # Pasar la solicitud al formulario
        return kwargs



