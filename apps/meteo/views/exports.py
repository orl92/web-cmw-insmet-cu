import csv
from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.views import View

from apps.meteo.models import Forecasts


class ForecastCSVExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'meteo.view_forecast'

    def get_queryset(self):
        date_string = self.request.GET.get('date')
        qs = Forecasts.objects.prefetch_related('regions', 'extended_days')
        if date_string:
            qs = qs.filter(date=date_string)
        return qs.order_by('date')

    def get(self, request):
        date_string = request.GET.get('date')
        if date_string:
            try:
                date.fromisoformat(date_string)
            except ValueError:
                return HttpResponseBadRequest('Fecha inválida.')
        forecasts = self.get_queryset()
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="pronosticos.csv"'
        response.write('\ufeff')
        writer = csv.writer(response)

        writer.writerow(['PRONÓSTICO POR REGIONES'])
        writer.writerow(
            [
                'Fecha',
                'Zona',
                'Período',
                'Temperatura (°C)',
                'Tiempo',
                'Viento (dd)',
                'Viento (ff)',
                'Mar',
            ]
        )
        for forecast in forecasts:
            for region in forecast.regions.all():
                writer.writerow(
                    [
                        forecast.date.strftime('%d/%m/%Y'),
                        region.get_region_display(),
                        region.get_period_display(),
                        region.temp,
                        region.weather,
                        region.wind_dir,
                        region.wind_speed,
                        region.sea_note or '',
                    ]
                )
        writer.writerow([])

        writer.writerow(['PRONÓSTICO EXTENDIDO'])
        writer.writerow(['Fecha', 'Día', 'Mínima (°C)', 'Máxima (°C)', 'Tiempo'])
        for forecast in forecasts:
            for day in forecast.extended_days.all():
                writer.writerow(
                    [
                        day.date.strftime('%d/%m/%Y'),
                        day.day_number,
                        day.min_temp,
                        day.max_temp,
                        day.weather,
                    ]
                )
        writer.writerow([])

        writer.writerow(['DATOS ASTRONÓMICOS'])
        writer.writerow(
            [
                'Fecha',
                'Fase Lunar',
                'Próxima Fase',
                'Fecha Próxima',
                'Salida Sol',
                'Puesta Sol',
                'Índice UV',
            ]
        )
        for forecast in forecasts:
            writer.writerow(
                [
                    forecast.date.strftime('%d/%m/%Y'),
                    forecast.lp,
                    forecast.nlp,
                    forecast.nlpd.strftime('%d/%m/%Y') if forecast.nlpd else '',
                    forecast.sunrise.strftime('%I:%M %p') if forecast.sunrise else '',
                    forecast.sunset.strftime('%I:%M %p') if forecast.sunset else '',
                    forecast.uv_index,
                ]
            )

        return response
