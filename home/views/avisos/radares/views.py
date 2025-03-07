from django.utils import timezone
from django.views.generic import ListView

from dashboard.models import RadarWarning

# Create your views here.

class RadarWarningListView(ListView):
    model = RadarWarning
    template_name = 'pages/home/avisos/radar.html'

    def get_queryset(self):
        return RadarWarning.objects.filter(valid_until__gte=timezone.now())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Aviso de Radar'
        context['parent'] = 'aviso'
        context['segment'] = 'radar'
        context['objects'] = self.get_queryset()
        return context