from django.utils import timezone
from django.views.generic import ListView

from dashboard.models import SpecialNotice

# Create your views here.
       
class SpecialNoticeListView(ListView):
    model = SpecialNotice
    template_name = 'pages/home/avisos/especial.html'

    def get_queryset(self):
        return SpecialNotice.objects.filter(valid_until__gte=timezone.now())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Aviso Especial'
        context['parent'] = 'aviso'
        context['segment'] = 'especial'
        context['objects'] = self.get_queryset()
        return context
