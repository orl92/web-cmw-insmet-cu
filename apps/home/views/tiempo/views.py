from django.utils import timezone
from django.views.generic import DetailView

from apps.meteo.models import WeatherReport


class WeatherReportDetailView(DetailView):
    model = WeatherReport

    def get_report_type(self):
        return self.kwargs.get('report_type', 'today')

    def get_template_names(self):
        type_map = {
            'today': 'pages/home/weather/today.html',
            'tomorrow': 'pages/home/weather/tomorrow.html',
            'commentary': 'pages/home/commentaries/weather.html',
            'note': 'pages/home/commentaries/note.html',
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
        context['objects'] = self.model.objects.filter(report_type=self.get_report_type())
        return context
