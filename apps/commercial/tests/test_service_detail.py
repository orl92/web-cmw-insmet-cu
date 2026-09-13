"""Tests for the servicios detail (Service) UI fix (016-public-ui-ux, Phase 5).

- Service.PERIOD_DAYS == 1 (business constant).
- Template renders summary sanitized and image with the responsive
  aspect-ratio + object-fit-cover pattern (no white bands on wide images).
"""

from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.commercial.models import Service


class ServiceDetailModelTests(TestCase):
    def test_period_days_constant(self):
        self.assertEqual(Service.PERIOD_DAYS, 1)

    def test_compute_end_date_agrometeo_no_overflow(self):
        # 31 ene + 2 meses -> 31 mar (sin desborde de fin de mes).
        self.assertEqual(
            Service.compute_end_date(date(2026, 1, 31), 2, 'agrometeo'), date(2026, 3, 31)
        )

    def test_compute_end_date_pronostico_daily(self):
        self.assertEqual(
            Service.compute_end_date(date(2026, 1, 1), 5, 'pronostico'), date(2026, 1, 6)
        )


class ServiceDetailTemplateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            'svcuser', 'svc@test.com', 'pass', first_name='Servicio', last_name='Prueba'
        )
        cls.service = Service.objects.create(
            user=cls.user,
            title='Servicio de prueba',
            summary='<b>Resumen</b><script>alert(1)</script>',
            service_type=Service.COMMERCIAL,
            price=100,
            image='services/test.png',
        )

    def test_template_renders_sanitized_summary_and_responsive_image(self):
        self.client.force_login(self.user)
        url = reverse('home:services_commercial_detail', args=[self.service.uuid])
        html = self.client.get(url).content.decode()
        self.assertIn('object-fit-cover', html)
        self.assertIn('aspect-ratio: 4/3', html)
        self.assertIn('Resumen', html)
        self.assertNotIn('<script>alert(1)</script>', html)
        # Category and period display rendered.
        self.assertIn('Período', html)
        self.assertIn('día', html)
