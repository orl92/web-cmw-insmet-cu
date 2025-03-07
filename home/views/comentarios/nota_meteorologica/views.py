from django.utils import timezone
from django.views.generic import *

from dashboard.models import WeatherNote

# Create your views here.   

class WeatherNoteDetailView(DetailView):
    model = WeatherNote
    template_name = 'pages/home/comentarios/nota_meteorologica/nota_meteorologica.html'
    context_object_name = 'weather_note'

    def get_object(self):
        return WeatherNote.objects.filter(date__date=timezone.now().date()).first()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nota Neteorológica'
        context['parent'] = 'comentario'
        context['segment'] = 'nota_meteorologica'
        context['objects'] = self.get_queryset()
        return context
