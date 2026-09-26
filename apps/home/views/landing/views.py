"""LandingView — landing pública en la raíz del portal.

La landing es ligera (sin amCharts ni tooling del dashboard): hero con el
pronóstico más reciente, avisos activos y servicios destacados. El home de
administración vive ahora en /home/ conservando el nombre 'index'.
"""

from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from apps.commercial.models import Service
from apps.meteo.models import Forecasts, Warning


class LandingView(TemplateView):
    template_name = 'pages/home/landing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Inicio'
        context['parent'] = ''
        context['segment'] = 'landing'

        try:
            context['latest_forecast'] = Forecasts.objects.prefetch_related(
                'regions', 'extended_days'
            ).latest('date')
        except ObjectDoesNotExist:
            context['latest_forecast'] = None

        context['active_warnings'] = (
            Warning.objects.filter(valid_until__gte=timezone.now())
            .select_related('user')
            .order_by('-date')[:3]
        )

        context['featured_services'] = (
            Service.objects.filter(record_active=True).select_related('user').order_by('-date')[:3]
        )

        context['og_url'] = self.request.build_absolute_uri(reverse('home:landing'))
        return context
