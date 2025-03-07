from django.utils import timezone
from django.views.generic import DetailView

from dashboard.models import WeatherCommentary

# Create your views here.

class WeatherCommentaryDetailView(DetailView):
    model = WeatherCommentary
    template_name = 'pages/home/comentarios/tiempo/comentario_tiempo.html'
    context_object_name = 'weather_commentary'

    def get_object(self):
        return WeatherCommentary.objects.filter(date__date=timezone.now().date()).first()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Comentario del Tiempo'
        context['parent'] = 'comentario'
        context['segment'] = 'comentario_tiempo'
        context['objects'] = self.get_queryset()
        return context

