from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.core.models import SiteConfiguration


def _disable_maintenance_mode():
    SiteConfiguration.objects.update_or_create(defaults={'maintenance_mode': False})


class ForecastCreateDateTests(TestCase):
    """Regresión: al re-renderizar tras error no se pierde la fecha enviada."""

    @classmethod
    def setUpTestData(cls):
        _disable_maintenance_mode()
        cls.admin = User.objects.create_superuser(
            'forecastadmin',
            'forecastadmin@example.com',
            'pass',
            first_name='Admin',
            last_name='User',
        )

    def test_invalid_post_keeps_submitted_date(self):
        self.client.force_login(self.admin)
        url = reverse('meteo:pronostico_create')
        data = {
            'date': '2026-08-09',
            'lp': '',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="09/08/2026"')
