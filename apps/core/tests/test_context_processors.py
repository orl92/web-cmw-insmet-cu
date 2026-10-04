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

    def _sub(self, status, record_active=True):
        return ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.service,
            start_date=timezone.now() - timedelta(days=30),
            record_active=record_active,
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

    def test_client_active_count_ignores_el_tiempo_transcurrido(self):
        """Activa = pagada y no anulada; el tiempo que pasa ya no la apaga.

        Este test usaba dos suscripciones pagadas y esperaba que sólo contara
        la primera, porque la segunda tenía el periodo ya vencido. Al quitarse
        `end_date` ese filtro por fechas no existe: lo único que saca una
        suscripción del conteo es la anulación (soft delete).
        """
        vigente = self._sub('paid')
        # El paso del tiempo no puede sacar a `vigente` del conteo: sin
        # `end_date` no hay nada que expire.
        vigente.start_date = timezone.now() - timedelta(days=3650)
        vigente.save(update_fields=['start_date'])
        self.assertTrue(vigente.is_active)

        self._sub('paid', record_active=False)

        context = self._context()
        self.assertEqual(context['client_active_count'], 1)
        self.assertEqual(context['client_pending_actions'], 0)
        # El total también es 1: la anulada no entra ni como vigente ni como
        # total, porque el manager por defecto filtra las filas con
        # `record_active=False`. "Mis Servicios" se apoya en ese total.
        self.assertEqual(context['client_subscriptions_count'], 1)
