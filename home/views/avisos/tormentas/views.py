from django.utils import timezone
from django.views.generic import ListView

from dashboard.models import StormWarning

# Create your views here.
       
class StormListView(ListView):
    model = StormWarning
    template_name = 'pages/home/avisos/tormenta.html'

    def get_queryset(self):
        return StormWarning.objects.filter(valid_until__gte=timezone.now())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Aviso de Tormenta'
        context['parent'] = 'aviso'
        context['segment'] = 'tormenta'
        context['objects'] = self.get_queryset()
        return context
