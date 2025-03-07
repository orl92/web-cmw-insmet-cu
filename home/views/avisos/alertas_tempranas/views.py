from django.utils import timezone
from django.views.generic import ListView

from dashboard.models import EarlyWarning

# Create your views here.
    
class EarlyWarningListView(ListView):
    model = EarlyWarning
    template_name = 'pages/home/avisos/alerta_temprana.html'

    def get_queryset(self):
        return EarlyWarning.objects.filter(valid_until__gte=timezone.now())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Aviso de Alerta Temprana'
        context['parent'] = 'aviso'
        context['segment'] = 'alerta_temprana'
        context['objects'] = self.get_queryset()
        return context
