from django.views.generic import TemplateView

from dashboard.models import Forecasts
from django.core.exceptions import ObjectDoesNotExist


# Create your views here.

class PagosView(TemplateView):
    template_name = 'pages/home/pagos/pagos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Pagos en linea'
        context['parent'] = ''
        context['segment'] = 'pagos'

        return context
