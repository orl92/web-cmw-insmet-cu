from datetime import timedelta

from django.utils import timezone
from django.views.generic import DetailView

from dashboard.models import WeatherTomorrow

# Create your views here.

class WeatherTomorrowDetailView(DetailView):
    model = WeatherTomorrow
    template_name = 'pages/home/tiempo/mañana/tiempo_m.html'
    context_object_name = 'weather_tomorrow'

    def get_object(self):
        tomorrow_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        tomorrow_end = tomorrow_start + timedelta(days=1)
        return WeatherTomorrow.objects.filter(date__range=(tomorrow_start, tomorrow_end)).first()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'El Tiempo para Mañana'
        context['parent'] = 'tiempo'
        context['segment'] = 'tiempo_m'
        context['objects'] = self.get_queryset()
        return context

