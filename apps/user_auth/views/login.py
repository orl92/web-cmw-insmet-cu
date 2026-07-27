from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic.base import RedirectView

from apps.core.utils import log_action


LOGIN_ACTION = 4
LOGOUT_ACTION = 5


class LoginFormView(LoginView):
    template_name = 'pages/login/sign_in.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Iniciar sesión'
        return context

    def get_success_url(self):
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url:
            return next_url
        if self.request.user.is_staff:
            return reverse_lazy('dashboard:index')
        return reverse_lazy('home:index')

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(self.request.user, self.request.user, LOGIN_ACTION, 'El usuario inició sesión.')
        messages.success(self.request, 'Has iniciado sesión correctamente.', extra_tags='success')
        return response


class LogoutRedirectView(RedirectView):
    url = settings.LOGOUT_REDIRECT_URL

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            log_action(self.request.user, self.request.user, LOGOUT_ACTION, 'El usuario cerró sesión.')
            messages.info(self.request, 'Has cerrado sesión con éxito.')
            logout(self.request)
        return super().get_redirect_url(*args, **kwargs)
