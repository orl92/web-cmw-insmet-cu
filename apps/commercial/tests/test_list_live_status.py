"""Endpoints AJAX de estado en vivo de los listados de facturas y suscripciones.

Los dos listados extienden `layouts/list.html`, que renderiza todas las filas y
pagina en el cliente, así que el JS puede refrescar sólo las celdas de Estado y
Acciones sin redibujar DataTables. Estos tests fijan el contrato de los dos
endpoints que alimentan ese refresco:

- Devuelven JSON con el fragmento ya renderizado de cada celda (una sola fuente
  de verdad: el partial que también usa el listado).
- Heredan los permisos de las vistas de listado y, en suscripciones, el mismo
  filtro por rol: un usuario del grupo `Clientes` no recibe filas ajenas.
- `pending` sólo es verdadero mientras la fila siga en estado transitorio.
"""

from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.commercial.models import (
    Invoice,
    InvoiceItem,
    Service,
    ServiceSubscription,
)
from apps.commercial.tests.factories import natural_customer
from apps.core.models import SiteConfiguration


def _disable_maintenance_mode():
    SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})


def _user(username, **kwargs):
    data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': f'{username}@live.test',
    }
    data.update(kwargs)
    return User.objects.create_user(username, password='pw', **data)  # pragma: allowlist secret


def _superuser(username):
    return User.objects.create_superuser(
        username, f'{username}@live.test', 'pw', first_name='Admin', last_name='Super'
    )


class _LiveStatusBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance_mode()
        cls.admin = _superuser('liveadmin')
        cls.service = Service.objects.create(
            user=cls.admin,
            title='Servicio live',
            summary='s',
            service_type=Service.COMMERCIAL,
            price=Decimal('10.00'),
            service_category='agrometeo',
            code='LIVE-01',
        )
        cls.customer = natural_customer(username='livecust')

    def _invoice(
        self,
        *,
        customer=None,
        number=None,
        pdf='',
        pdf_status=Invoice.PdfStatus.PENDING,
        email_status=Invoice.EmailStatus.PENDING,
    ):
        return Invoice.objects.create(
            customer=customer or self.customer,
            amount=Decimal('10.00'),
            number=number or f'LIVE-{Invoice.objects.count() + 1}',
            pdf=pdf or None,
            pdf_status=pdf_status,
            email_status=email_status,
        )

    def _subscription(self, *, customer=None, payment_status='pending', record_active=True):
        return ServiceSubscription.objects.create(
            customer=customer or self.customer,
            service=self.service,
            start_date=timezone.now(),
            payment_status=payment_status,
            quantity=1,
            record_active=record_active,
        )

    def _link_invoice(self, subscription, *, number, pdf='facturas/live.pdf', pdf_status='ready'):
        invoice = Invoice.objects.create(
            customer=subscription.customer,
            subscription=subscription,
            amount=Decimal('10.00'),
            number=number,
            pdf=pdf or None,
            pdf_status=pdf_status,
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            subscription=subscription,
            codigo='LIVE-01',
            descripcion='Servicio live',
            cantidad=1,
            unidad_medida='U',
            precio=Decimal('10.00'),
            importe=Decimal('10.00'),
        )
        return invoice

    def _grant_view_subscription(self, user):
        """Da `view_subscription` por grupo `Clientes` (el camino no-staff)."""
        group, _ = Group.objects.get_or_create(name='Clientes')
        perm = ContentType.objects.get_for_model(ServiceSubscription).permission_set.get(
            codename='view_subscription'
        )
        group.permissions.add(perm)
        user.groups.add(group)
        return user


class InvoiceStatusEndpointTests(_LiveStatusBase):
    def setUp(self):
        self.url = reverse('commercial:ajax_invoice_status')
        self.client.force_login(self.admin)

    def test_anonymous_is_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_staff_without_view_invoice_is_redirected_to_login(self):
        # `permission_required` sin `raise_exception` redirige al login (patrón
        # del módulo, igual que `ajax_pending_subscriptions`), no responde 403.
        staff = _user('noinvperm', is_staff=True)
        self.client.force_login(staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_missing_uuids_returns_empty_rows_and_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'rows': [], 'pending': False})

    def test_invalid_uuid_is_ignored_without_500(self):
        response = self.client.get(self.url, {'uuids': 'no-es-uuid'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['rows'], [])

    def test_pending_invoice_reports_pending_and_no_download(self):
        invoice = self._invoice(pdf='', pdf_status=Invoice.PdfStatus.PENDING)
        response = self.client.get(self.url, {'uuids': str(invoice.uuid)})
        data = response.json()
        self.assertTrue(data['pending'])
        row = data['rows'][0]
        self.assertEqual(row['uuid'], str(invoice.uuid))
        self.assertTrue(row['pending'])
        self.assertNotIn(
            reverse('commercial:factura_download', args=[invoice.uuid]), row['actions_html']
        )

    def test_ready_invoice_reports_not_pending_with_download(self):
        invoice = self._invoice(
            pdf='facturas/live.pdf',
            pdf_status=Invoice.PdfStatus.READY,
            email_status=Invoice.EmailStatus.SENT,
        )
        response = self.client.get(self.url, {'uuids': str(invoice.uuid)})
        data = response.json()
        self.assertFalse(data['pending'])
        row = data['rows'][0]
        self.assertFalse(row['pending'])
        self.assertIn(
            reverse('commercial:factura_download', args=[invoice.uuid]), row['actions_html']
        )
        # La celda Estado viaja renderizada desde el mismo partial del listado.
        self.assertIn('Pendiente', row['status_html'])

    def test_email_pending_keeps_row_pending_even_with_ready_pdf(self):
        invoice = self._invoice(
            pdf='facturas/live.pdf',
            pdf_status=Invoice.PdfStatus.READY,
            email_status=Invoice.EmailStatus.PENDING,
        )
        response = self.client.get(self.url, {'uuids': str(invoice.uuid)})
        self.assertTrue(response.json()['pending'])


class SubscriptionStatusEndpointTests(_LiveStatusBase):
    def setUp(self):
        self.url = reverse('commercial:ajax_subscription_status')
        self.sub = self._subscription(payment_status='pending')

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_staff_without_view_subscription_is_redirected_to_login(self):
        # Idem invoice: el decorador sin `raise_exception` redirige al login.
        staff = _user('nosubperm', is_staff=True)
        self.client.force_login(staff)
        response = self.client.get(self.url, {'uuids': str(self.sub.uuid)})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_pending_subscription_without_pdf_hides_approve_and_reports_pending(self):
        # "Sin PDF" es con factura emitida y PDF aún generándose: sin factura no
        # hay nada que esperar y la fila no se considera transitoria.
        self._link_invoice(self.sub, number='LIVE-SUB-GEN', pdf_status=Invoice.PdfStatus.PENDING)
        self.client.force_login(self.admin)
        response = self.client.get(self.url, {'uuids': str(self.sub.uuid)})
        data = response.json()
        self.assertTrue(data['pending'])
        row = data['rows'][0]
        self.assertTrue(row['pending'])
        self.assertNotIn('title="Aprobar Pago"', row['actions_html'])

    def test_pending_subscription_with_ready_pdf_shows_approve_and_is_not_pending(self):
        self._link_invoice(self.sub, number='LIVE-SUB-1')
        self.client.force_login(self.admin)
        response = self.client.get(self.url, {'uuids': str(self.sub.uuid)})
        data = response.json()
        self.assertFalse(data['pending'])
        row = data['rows'][0]
        self.assertFalse(row['pending'])
        self.assertIn('title="Aprobar Pago"', row['actions_html'])

    def test_client_group_only_receives_own_subscriptions(self):
        other_customer = natural_customer(username='liveother')
        other_sub = self._subscription(customer=other_customer, payment_status='pending')

        client_user = self.customer.user
        group, _ = Group.objects.get_or_create(name='Clientes')
        perm = ContentType.objects.get_for_model(ServiceSubscription).permission_set.get(
            codename='view_subscription'
        )
        group.permissions.add(perm)
        client_user.groups.add(group)

        self.client.force_login(client_user)
        response = self.client.get(self.url, {'uuids': f'{self.sub.uuid},{other_sub.uuid}'})
        self.assertEqual(response.status_code, 200)
        uuids = [row['uuid'] for row in response.json()['rows']]
        self.assertIn(str(self.sub.uuid), uuids)
        self.assertNotIn(str(other_sub.uuid), uuids)

    def test_invalid_uuid_is_ignored_without_500(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url, {'uuids': 'no-es-uuid'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['rows'], [])

    def test_duplicate_uuids_return_a_single_row(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url, {'uuids': f'{self.sub.uuid},{self.sub.uuid}'})
        self.assertEqual(len(response.json()['rows']), 1)

    def test_pending_without_invoice_is_not_pending(self):
        # Sin factura no hay nada asíncrono que esperar: si no, el polling
        # quedaría vivo para siempre (el PDF nunca va a llegar).
        self.client.force_login(self.admin)
        response = self.client.get(self.url, {'uuids': str(self.sub.uuid)})
        self.assertFalse(response.json()['pending'])

    def test_cancelled_subscription_hides_approve_even_with_ready_pdf(self):
        cancelled = self._subscription(payment_status='pending', record_active=False)
        self._link_invoice(cancelled, number='LIVE-SUB-CANCEL')
        self.client.force_login(self.admin)
        response = self.client.get(self.url, {'uuids': str(cancelled.uuid)})
        self.assertNotIn('title="Aprobar Pago"', response.json()['rows'][0]['actions_html'])

    def test_paid_subscription_hides_approve_even_with_ready_pdf(self):
        paid = self._subscription(payment_status='paid')
        self._link_invoice(paid, number='LIVE-SUB-PAID')
        self.client.force_login(self.admin)
        response = self.client.get(self.url, {'uuids': str(paid.uuid)})
        self.assertNotIn('title="Aprobar Pago"', response.json()['rows'][0]['actions_html'])

    def test_non_staff_without_client_group_is_denied(self):
        user = _user('liveoutsider')
        perm = ContentType.objects.get_for_model(ServiceSubscription).permission_set.get(
            codename='view_subscription'
        )
        user.user_permissions.add(perm)
        self.client.force_login(user)
        response = self.client.get(self.url, {'uuids': str(self.sub.uuid)})
        self.assertEqual(response.status_code, 403)


class SubscriptionListMarkersTests(_LiveStatusBase):
    """La página del listado tiene que marcar las filas que el JS debe refrescar.

    Si el marcador `data-live-pending` y el `pending` del endpoint divergen, el
    polling nunca arranca (o no se detiene). Estos dos tests atan los dos lados.
    """

    def setUp(self):
        self.url = reverse('commercial:suscripcion_list')
        self.client.force_login(self.admin)

    def test_marks_pending_while_the_invoice_pdf_is_generating(self):
        sub = self._subscription(payment_status='pending')
        self._link_invoice(sub, number='LIVE-MARK-1', pdf_status=Invoice.PdfStatus.PENDING)
        html = self.client.get(self.url).content.decode()
        self.assertIn('data-live-pending="1"', html)
        self.assertNotIn('title="Aprobar Pago"', html)

    def test_stops_marking_pending_once_the_pdf_is_ready(self):
        sub = self._subscription(payment_status='pending')
        self._link_invoice(sub, number='LIVE-MARK-2')
        html = self.client.get(self.url).content.decode()
        self.assertNotIn('data-live-pending="1"', html)
        self.assertIn('title="Aprobar Pago"', html)
