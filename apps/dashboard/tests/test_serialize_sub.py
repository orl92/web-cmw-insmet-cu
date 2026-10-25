"""El panel del dashboard no puede mostrar `N/A` donde va el nombre del cliente.

`Customer.company_name` sólo existe para personas jurídicas: en una natural es
NULL, así que el listado de suscripciones del panel mostraba `N/A` en lugar del
nombre de la persona. `Customer.display_name` ya resuelve ese nombre.
"""

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.commercial.models import Service, ServiceSubscription
from apps.commercial.tests.factories import make_user, natural_customer
from apps.dashboard.views.dashboard.dashboard import serialize_sub


class SerializeSubCustomerTests(TestCase):
    """`serialize_sub` es lo que el panel muestra en la lista de suscripciones."""

    @classmethod
    def setUpTestData(cls):
        cls.user = make_user('panel.natural', first_name='Ana', last_name='Norte')
        cls.customer = natural_customer(cls.user)
        cls.service = Service.objects.create(
            user=cls.user,
            title='Servicio Panel',
            summary='S',
            service_type='commercial',
            code='PNL1',
            price=Decimal('25.00'),
        )

    def _sub(self, customer):
        return ServiceSubscription.objects.create(
            customer=customer,
            service=self.service,
            start_date=timezone.now(),
            payment_status='paid',
        )

    def test_cliente_natural_muestra_su_nombre(self):
        data = serialize_sub(self._sub(self.customer))
        self.assertEqual(data['customer'], 'Ana Norte')
        self.assertNotIn('N/A', data['customer'])
        self.assertNotIn('None', data['customer'])

    def test_el_nombre_escapa_el_html(self):
        """El panel inyecta el valor en el DOM: el nombre va escapado."""
        customer = natural_customer(
            make_user('panel.escape', first_name='Ana <b>Norte</b>', last_name='')
        )
        data = serialize_sub(self._sub(customer))
        self.assertNotIn('<b>', data['customer'])
        self.assertIn('&lt;b&gt;', data['customer'])

    def test_cliente_sin_nombre_cae_al_username(self):
        """`display_name` degrada al username, no a un placeholder vacío."""
        customer = natural_customer(make_user('panel.sin.nombre', first_name='', last_name=''))
        data = serialize_sub(self._sub(customer))
        self.assertEqual(data['customer'], 'panel.sin.nombre')
        self.assertNotIn('None', data['customer'])
        self.assertNotIn('N/A', data['customer'])
