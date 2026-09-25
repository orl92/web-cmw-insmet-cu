from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.http import HttpResponseNotAllowed
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic.base import RedirectView

from apps.core.models import ActivityLog
from apps.core.utils import log_activity_from_request


def _safe_next_url(next_url, request):
    """Solo permite rutas internas del mismo host; bloquea open redirect."""
    if not next_url:
        return ''
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return ''
    return next_url


class LoginFormView(LoginView):
    template_name = 'pages/user_auth/login/sign_in.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Iniciar sesión'
        return context

    def get_success_url(self):
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url and _safe_next_url(next_url, self.request):
            return str(next_url)
        if self.request.user.is_staff:
            return str(reverse_lazy('dashboard:index'))
        return str(reverse_lazy('home:index'))

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity_from_request(
            self.request,
            self.request.user,
            ActivityLog.ACTIVITY_LOGIN,
            'El usuario inició sesión.',
        )
        messages.success(self.request, 'Has iniciado sesión correctamente.', extra_tags='success')
        return response


class LogoutRedirectView(RedirectView):
    url = settings.LOGOUT_REDIRECT_URL

    def dispatch(self, request, *args, **kwargs):
        if request.method != 'POST':
            # El cierre de sesión muta el estado: un GET nunca debe poder
            # forzar un logout (p. ej. <img src="/accounts/logout/">).
            return HttpResponseNotAllowed(['POST'])
        return super().dispatch(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            # El log de actividad se escribe ANTES de logout(): log_action usa
            # request.user como actor y tras el flush quedaría AnonymousUser.
            log_activity_from_request(
                self.request,
                self.request.user,
                ActivityLog.ACTIVITY_LOGOUT,
                'El usuario cerró sesión.',
            )
            logout(self.request)
            # El mensaje se añade DESPUÉS del flush: se guarda en la sesión
            # nueva y sí llega al redirect (si se ponía antes, session.flush()
            # lo destruía).
            messages.info(self.request, 'Has cerrado sesión con éxito.')
        return super().get_redirect_url(*args, **kwargs)
