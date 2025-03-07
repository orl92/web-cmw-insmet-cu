from django.utils import timezone
from django.views.generic import ListView

from dashboard.models import TropicalCyclone

# Create your views here.
    
class TropicalCycloneListView(ListView):
    model = TropicalCyclone
    template_name = 'pages/home/avisos/ciclon_tropical.html'

    def get_queryset(self):
        return TropicalCyclone.objects.filter(valid_until__gte=timezone.now())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Aviso de Ciclón Tropical'
        context['parent'] = 'aviso'
        context['segment'] = 'ciclon_tropical'
        context['objects'] = self.get_queryset()
        return context