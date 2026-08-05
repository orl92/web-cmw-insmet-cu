from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.models import SiteConfiguration
from apps.meteo.models import ForecastExtendedDay, ForecastRegions, Forecasts


def _disable_maintenance_mode():
    SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})


class ForecastCSVExportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance_mode()
        cls.admin = User.objects.create_superuser(
            'admin',
            'admin@example.com',
            'pass',
            first_name='Admin',
            last_name='User',
        )

    def test_export_by_date(self):
        forecast = Forecasts.objects.create(
            date=timezone.now().date(),
            lp='Luna Nueva',
            nlp='Creciente',
            nlpd=timezone.now().date(),
            sunrise='06:30',
            sunset='19:00',
            uv_index=6,
        )
        ForecastRegions.objects.create(
            forecast=forecast,
            region='north',
            period='morning',
            temp=25,
            weather='PN',
            wind_dir='NE',
            wind_speed='10',
            sea_note='1',
        )
        ForecastExtendedDay.objects.create(
            forecast=forecast,
            day_number=1,
            date=timezone.now().date(),
            min_temp=20,
            max_temp=28,
            weather='PN',
        )
        self.client.force_login(self.admin)
        url = reverse('meteo:pronostico_export_csv')
        response = self.client.get(url, {'date': timezone.now().date().strftime('%Y-%m-%d')})
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8-sig')
        self.assertIn('Costa Norte', content)
        self.assertIn('PRONÓSTICO EXTENDIDO', content)
        self.assertIn('DATOS ASTRONÓMICOS', content)
        self.assertIn('Luna Nueva', content)

    def test_export_requires_login(self):
        self.client.logout()
        url = reverse('meteo:pronostico_export_csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_export_invalid_date_returns_bad_request(self):
        self.client.force_login(self.admin)
        url = reverse('meteo:pronostico_export_csv')
        response = self.client.get(url, {'date': 'abc'})
        self.assertEqual(response.status_code, 400)
