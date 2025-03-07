from django.utils import timezone
from django.views.generic import DetailView

from dashboard.models import WeatherToday

# Create your views here.   

class WeatherTodayDetailView(DetailView):
    model = WeatherToday
    template_name = 'pages/home/tiempo/hoy/tiempo_h.html'
    context_object_name = 'weather_today'

    def get_object(self):
        return WeatherToday.objects.filter(date__date=timezone.now().date()).first()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'El Tiempo para Hoy'
        context['parent'] = 'tiempo'
        context['segment'] = 'tiempo_h'
        context['objects'] = self.get_queryset()
        return context
