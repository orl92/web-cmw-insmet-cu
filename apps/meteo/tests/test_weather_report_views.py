from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.models import SiteConfiguration
from apps.meteo.models import WeatherReport


def _disable_maintenance_mode():
    SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})


class WeatherReportDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance_mode()
        cls.admin = User.objects.create_superuser(
            'admin', 'admin@example.com', 'pass',
            first_name='Admin', last_name='User',
        )
        cls.reports = {
            'today': WeatherReport.objects.create(
                report_type='today', summary='Resumen hoy', user=cls.admin,
                date=timezone.now(),
            ),
            'tomorrow': WeatherReport.objects.create(
                report_type='tomorrow', summary='Resumen mañana', user=cls.admin,
                date=timezone.now(),
            ),
            'commentary': WeatherReport.objects.create(
                report_type='commentary', summary='Comentario', user=cls.admin,
                date=timezone.now(),
            ),
            'note': WeatherReport.objects.create(
                report_type='note', summary='Nota', user=cls.admin,
                date=timezone.now(),
            ),
        }

    def test_detail_pages_render_for_each_report_type(self):
        urls = {
            'today': 'meteo:tiempo_hoy_detail',
            'tomorrow': 'meteo:tiempo_manana_detail',
            'commentary': 'meteo:comentario_tiempo_detail',
            'note': 'meteo:nota_meteorologica_detail',
        }
        self.client.force_login(self.admin)
        for report_type, url_name in urls.items():
            obj = self.reports[report_type]
            url = reverse(url_name, kwargs={'uuid': obj.uuid})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, msg=f'{report_type} detail 500')
            self.assertContains(response, 'Información General')
            self.assertContains(response, 'Volver al Listado')
            self.assertContains(response, 'Editar')
