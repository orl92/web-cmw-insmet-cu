"""menu_notifications context processor — mis-servicios-cliente (task 4.8).

client_pending_actions se computa en el path normal (sin excepción) como la
suma de requested + pending del cliente autenticado con commercial_customer.
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.commercial.models import Customer, Service, ServiceSubscription
from apps.core.context_processors import menu_notifications


class MenuNotificationsClientCountsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.provider = User.objects.create_user(
            'menunotifprov', 'menunotifprov@test.com', 'pass', first_name='P', last_name='N'
        )
        self.client_user = User.objects.create_user(
            'menunotifcli', 'menunotifcli@test.com', 'pass', first_name='C', last_name='N'
        )
        self.customer = Customer.objects.create(
            user=self.client_user,
            client_type=Customer.ClientType.NATURAL,
            account='1234567890123456',
            agency_bank='BANDEC',
            address='Addr',
            phone='12345678',
        )
        self.service = Service.objects.create(
            user=self.provider,
            title='Servicio notificación',
            summary='Sum',
            service_type=Service.COMMERCIAL,
            price=10,
        )

    def _sub(self, status, end_date=None):
        return ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.service,
            start_date=timezone.now() - timedelta(days=30),
            end_date=end_date or timezone.now() + timedelta(days=30),
            payment_status=status,
            payment_method='transfer',
        )

    def _context(self):
        request = self.factory.get('/')
        request.user = self.client_user
        return menu_notifications(request)

    def test_client_pending_actions_sums_requested_and_pending(self):
        self._sub('requested')
        self._sub('pending')
        context = self._context()
        self.assertEqual(context['client_requested_count'], 1)
        self.assertEqual(context['client_pending_count'], 1)
        self.assertEqual(context['client_pending_actions'], 2)

    def test_client_counts_distinguish_active_and_expired(self):
        self._sub('paid')
        self._sub('expired', end_date=timezone.now() - timedelta(days=1))
        context = self._context()
        self.assertEqual(context['client_active_count'], 1)
        self.assertEqual(context['client_expired_count'], 1)
        self.assertEqual(context['client_pending_actions'], 0)
