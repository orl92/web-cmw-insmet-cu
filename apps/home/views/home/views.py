from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView

from apps.meteo.models import Forecasts

# Create your views here.


class IndexView(TemplateView):
    template_name = 'pages/home/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Inicio'
        context['parent'] = ''
        context['segment'] = 'index'

        # Datos meteorológicos comunes
        try:
            context['latest_forecast'] = Forecasts.objects.prefetch_related(
                'regions', 'extended_days'
            ).latest('date')
        except ObjectDoesNotExist:
            context['latest_forecast'] = None

        return context
