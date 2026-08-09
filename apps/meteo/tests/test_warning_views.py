from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.models import SiteConfiguration
from apps.meteo.models import Warning


def _disable_maintenance_mode():
    SiteConfiguration.objects.update_or_create(defaults={'maintenance_mode': False})


class WarningFormDateTests(TestCase):
    """Regresión: el valor de valid_until debe persistir en edición y re-render."""

    @classmethod
    def setUpTestData(cls):
        _disable_maintenance_mode()
        cls.admin = User.objects.create_superuser(
            'warnadmin',
            'warnadmin@example.com',
            'pass',
            first_name='Admin',
            last_name='User',
        )
        cls.warning = Warning.objects.create(
            warning_type='early',
            user=cls.admin,
            summary='Resumen del aviso',
            valid_until=timezone.datetime(
                2026, 8, 5, 14, 30, tzinfo=timezone.get_current_timezone()
            ),
        )

    def test_update_get_prepopulates_valid_until(self):
        self.client.force_login(self.admin)
        url = reverse('meteo:alerta_temprana_update', args=[self.warning.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="05/08/2026 02:30 PM"')

    def test_invalid_post_keeps_submitted_valid_until(self):
        self.client.force_login(self.admin)
        url = reverse('meteo:alerta_temprana_update', args=[self.warning.uuid])
        data = {
            'summary': '',
            'valid_until': '2026-08-05T14:30',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="05/08/2026 02:30 PM"')
