from django.shortcuts import render
from django.urls import reverse
from dashboard.models import SiteConfiguration

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Permitir el acceso al superusuario
        if request.user.is_authenticated and request.user.is_superuser:
            return self.get_response(request)

        # Excluir la página de inicio de sesión (y otras URLs necesarias)
        excluded_paths = [
            reverse('login'),  # Asegúrate de que el nombre de la URL sea 'login'
        ]
        if request.path in excluded_paths:
            return self.get_response(request)

        # Verificar el estado del modo de mantenimiento
        config = SiteConfiguration.objects.first()
        if config and config.maintenance_mode:
            return render(request, 'layouts/maintenance.html', status=503)

        return self.get_response(request)
