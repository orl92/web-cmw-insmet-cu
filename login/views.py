from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.admin.models import ADDITION, DELETION
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.base import RedirectView
from common.utils import log_action
from django.contrib import messages

# Create your views here.

# Vista de Inicio de Sesión
class LoginFormView(SuccessMessageMixin, LoginView):
    template_name = 'pages/login/sign-in.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Iniciar sesión'
        return context

    def get_success_url(self):
        # Redirige al dashboard si el usuario es staff, de lo contrario al index
        if self.request.user.is_staff:
            return reverse_lazy('dashboard')
        else:
            return reverse_lazy('index')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Registrar la acción de inicio de sesión
        log_action(
            user=self.request.user,
            obj=self.request.user,
            action_flag=4,  # Inicio de sesión
            message="El usuario inició sesión."
        )
        # Mostrar un mensaje de retroalimentación al usuario
        messages.success(self.request, 'Has iniciado sesión correctamente.', extra_tags='success')
        return response

# Vista de Cierre de Sesión con Redirección
class LogoutRedirectView(RedirectView):
    pattern_name = 'index'  # Define la URL hacia la que redirigir después de cerrar sesión

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Registrar la acción de cierre de sesión
            log_action(
                user=request.user,
                obj=request.user,
                action_flag=5,  # Cierre de sesión
                message="El usuario cerró sesión."
            )
            # Mostrar un mensaje de retroalimentación al usuario
            messages.info(request, 'Has cerrado sesión con éxito.')
        
        # Cerrar sesión
        logout(request)
        return super().dispatch(request, *args, **kwargs)
