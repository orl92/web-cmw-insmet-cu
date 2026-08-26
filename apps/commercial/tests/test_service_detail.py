"""Tests for the servicios detail (Service) UI fix (016-public-ui-ux, Phase 5).

- Service.PERIOD_DAYS == 30 (business constant).
- Template renders summary sanitized and image with object-fit: contain.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.commercial.models import Service


class ServiceDetailModelTests(TestCase):
    def test_period_days_constant(self):
        self.assertEqual(Service.PERIOD_DAYS, 30)


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

    def test_template_renders_sanitized_summary_and_contain(self):
        self.client.force_login(self.user)
        url = reverse('home:services_commercial_detail', args=[self.service.uuid])
        html = self.client.get(url).content.decode()
        self.assertIn('object-fit: contain', html)
        # XSS-safe: summary text present, disallowed <script> neutralized.
        # (Legit <script src=...> library tags may still appear.)
        self.assertIn('Resumen', html)
        self.assertNotIn('<script>alert(1)</script>', html)
        # Period constant rendered.
        self.assertIn('Período estándar: <strong>30 días</strong>', html)
        self.assertIn('Monto estimado (30 días)', html)
