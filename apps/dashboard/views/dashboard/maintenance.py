from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView

from apps.common.utils import log_action
from apps.dashboard.models import SiteConfiguration


class MaintenanceModeToggleView(UserPassesTestMixin, TemplateView):
    template_name = 'pages/dashboard/maintenance_mode/toggle_maintenance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config, created = SiteConfiguration.objects.get_or_create()
        context['config'] = config
        context['title'] = 'Modo de Mantenimiento'
        context['parent'] = ''
        context['segment'] = 'maintenance'
        return context

    def post(self, request, *args, **kwargs):
        config, created = SiteConfiguration.objects.get_or_create()
        if config:
            maintenance_mode = 'maintenance_mode' in request.POST
            config.maintenance_mode = maintenance_mode
            config.save()

            log_action(
                user=request.user,
                obj=request.user,
                action_flag=6,
                message=f"El usuario {request.user.username} {'activó' if maintenance_mode else 'desactivó'} el modo de mantenimiento."
            )

            state = "activado" if config.maintenance_mode else "desactivado"
            messages.success(request, f"El modo de mantenimiento ha sido {state}.")

        return redirect('dashboard:toggle_maintenance_mode')

    def test_func(self):
        return self.request.user.is_superuser
