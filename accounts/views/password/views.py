from django.contrib import messages
from django.contrib.admin.models import CHANGE
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordResetView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from accounts.forms.password.forms import (AdminPasswordChangeForm,
                                           UserPasswordChangeForm)
from common.utils import log_action

# Create your views here.

class PasswordChangeView(LoginRequiredMixin, FormView):
    template_name = 'pages/accounts/password/password_change.html'
    form_class = UserPasswordChangeForm
    success_url = reverse_lazy('profile')
    url_redirect = success_url

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            if request.user.profile.is_ldap:
                messages.warning(request, "No puedes cambiar tu contraseña porque estás autenticado mediante LDAP.")
                return redirect('profile')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
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

    def dispatch(self, request, *args, **kwargs):
        user = get_object_or_404(User, profile__uuid=self.kwargs.get('uuid'))
        if hasattr(user, 'profile') and user.profile.is_ldap:
            messages.error(request, f"No puedes cambiar la contraseña de '{user.username}' porque es un usuario LDAP.")
            return redirect('users')  # o a donde prefieras
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = get_object_or_404(User, profile__uuid=self.kwargs.get('uuid'))
        kwargs['instance'] = user
        return kwargs

    def form_valid(self, form):
        user = form.save()
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
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            if request.user.profile.is_ldap:
                messages.warning(request, "No puedes restablecer tu contraseña porque estás autenticado mediante LDAP.")
                return redirect('profile')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs