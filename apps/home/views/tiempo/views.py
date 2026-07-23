from django.utils import timezone
from django.views.generic import DetailView

from apps.dashboard.models import WeatherReport


class WeatherReportDetailView(DetailView):
    model = WeatherReport

    def get_report_type(self):
        return self.kwargs.get('report_type', 'today')

    def get_template_names(self):
        type_map = {
            'today': 'pages/home/tiempo/hoy/tiempo_h.html',
            'tomorrow': 'pages/home/tiempo/mañana/tiempo_m.html',
            'commentary': 'pages/home/comentarios/tiempo/comentario_tiempo.html',
            'note': 'pages/home/comentarios/nota_meteorologica/nota_meteorologica.html',
        }
        return [type_map[self.get_report_type()]]

    def get_context_object_name(self, obj):
        name_map = {
            'today': 'weather_today',
            'tomorrow': 'weather_tomorrow',
            'commentary': 'weather_commentary',
            'note': 'weather_note',
        }
        return name_map[self.get_report_type()]

    def get_object(self):
        return WeatherReport.objects.filter(
            report_type=self.get_report_type(),
            date__date=timezone.now().date()
        ).select_related('user').first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        type_map = {
            'today': ('El Tiempo para Hoy', 'weather_today', 'tiempo'),
            'tomorrow': ('El Tiempo para Mañana', 'weather_tomorrow', 'tiempo'),
            'commentary': ('Comentario del Tiempo', 'weather_commentary', 'tiempo'),
            'note': ('Nota Meteorológica', 'weather_note', 'tiempo'),
        }
        title, segment, parent = type_map[self.get_report_type()]
        context['title'] = title
        context['parent'] = parent
        context['segment'] = segment
        context['objects'] = self.get_queryset()
        return context
