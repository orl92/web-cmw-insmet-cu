"""Desglose de cobro por línea en el listado de facturación.

Una factura que agrupa suscripciones (lote o manual multi-servicio) hoy muestra
solo la insignia `Pendiente`: no dice cuántas líneas son ni cuál falta cobrar, y
no hay camino a "Aprobar Pago" desde Facturación. Estos tests fijan el contrato:

- El desglose vive dentro de la celda Estado (`status_cell.html`) y sale del
  partial `line_payments.html`, así que hereda el refresco en vivo de
  `ajax_invoice_status` sin JS nuevo.
- El resumen `n/N cobradas` sale de `items_paid`/`items_total` que anota
  `with_display_status()`: la misma fuente que decide `status_display`, no un
  recálculo paralelo.
- El link a `commercial:suscripcion_approve` se ofrece sólo con
  `commercial.change_subscription` —el permiso que exige la vista—, la factura
  emitida (`pdf_ready`) y no anulada, y sólo sobre la línea en `pending`.
- Sin consultas por línea: el `Prefetch` de las dos querysets (listado y
  endpoint) evita que cada línea pague su propia consulta por
  `subscription__service`.
"""

from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.commercial.models import (
    Invoice,
    InvoiceItem,
    Service,
    ServiceSubscription,
)
from apps.commercial.tests.factories import make_user, natural_customer
from apps.commercial.views.invoices import InvoiceListView
from apps.core.models import SiteConfiguration


def _superuser(username):
    return User.objects.create_superuser(
        username,
        f'{username}@example.com',
        'pw',  # pragma: allowlist secret
        first_name='Admin',
        last_name='Super',
    )


class _LinePaymentsBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        cls.admin = _superuser('lineadmin')
        cls.customer = natural_customer(
            make_user('linecust', first_name='Ana', last_name='Norte'),
        )
        cls.service = Service.objects.create(
            user=cls.admin,
            title='Pronóstico diario',
            summary='Pronóstico puntual',
            service_type='commercial',
            service_category='pronostico',
            code='LINE-01',
            price=Decimal('10.00'),
        )

    def _subscription(self, *, payment_status='pending', record_active=True):
        return ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.service,
            quantity=1,
            payment_status=payment_status,
            record_active=record_active,
        )

    def _invoice(
        self,
        *,
        number,
        subscription=None,
        pdf='factura/line.pdf',
        pdf_status=Invoice.PdfStatus.READY,
        is_cancelled=False,
    ):
        return Invoice.objects.create(
            customer=self.customer,
            subscription=subscription,
            number=number,
            amount=Decimal('10.00'),
            pdf=pdf or None,
            pdf_status=pdf_status,
            is_cancelled=is_cancelled,
        )

    def _item(self, invoice, subscription, *, descripcion=None, importe=Decimal('10.00')):
        return InvoiceItem.objects.create(
            invoice=invoice,
            subscription=subscription,
            codigo='LINE-01',
            descripcion=descripcion or subscription.service.title,
            cantidad=Decimal('1'),
            unidad_medida='U',
            precio=importe,
            importe=importe,
        )

    def _grant_view_invoice(self, user):
        perm = ContentType.objects.get_for_model(Invoice).permission_set.get(
            codename='view_invoice'
        )
        user.user_permissions.add(perm)
        return user


class LinePaymentsModelTests(_LinePaymentsBase):
    """La propiedad del modelo traduce suscripción -> estado de la línea."""

    def _linea(self, payment_status, record_active=True):
        sub = self._subscription(payment_status=payment_status, record_active=record_active)
        invoice = self._invoice(number=f'LP-{payment_status}-{record_active}')
        self._item(invoice, sub)
        return invoice, invoice.line_payments[0]

    def test_linea_pagada_se_reporta_pagado(self):
        sub_pending = self._subscription(payment_status='pending')
        invoice = self._invoice(number='LP-EST-PAID')
        self._item(invoice, sub_pending, importe=Decimal('7.50'))
        sub_pending.payment_status = 'paid'
        sub_pending.save(update_fields=['payment_status'])

        line = invoice.line_payments[0]
        self.assertEqual(line['estado'], 'pagado')
        self.assertEqual(line['uuid'], str(sub_pending.uuid))
        self.assertEqual(line['importe'], Decimal('7.50'))
        self.assertEqual(line['servicio'], self.service.title)
        self.assertEqual(line['descripcion'], self.service.title)

    def test_linea_pendiente_se_reporta_pendiente(self):
        _, line = self._linea('pending')
        self.assertEqual(line['estado'], 'pendiente')

    def test_suscripcion_dada_de_baja_se_reporta_cancelada(self):
        _, line = self._linea('pending', record_active=False)
        self.assertEqual(line['estado'], 'cancelada')

    def test_suscripcion_dada_de_baja_no_es_aprobable(self):
        # `aprobable` exige `record_active`: una baja lógica con el pago todavía
        # en `pending` no puede ofrecer "Aprobar pago" (el listado de
        # suscripciones tampoco lo ofrece).
        _, line = self._linea('pending', record_active=False)
        self.assertFalse(line['aprobable'])

    def test_ignora_las_lineas_sin_suscripcion(self):
        sub = self._subscription(payment_status='pending')
        invoice = self._invoice(number='LP-SIN-SUB')
        self._item(invoice, sub)
        InvoiceItem.objects.create(
            invoice=invoice,
            subscription=None,
            codigo='LIBRE',
            descripcion='Renglón libre',
            cantidad=Decimal('1'),
            unidad_medida='U',
            precio=Decimal('3.00'),
            importe=Decimal('3.00'),
        )

        lines = invoice.line_payments
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]['descripcion'], self.service.title)

    def _factura_de_una_linea(self, payment_status, *, record_active=True):
        sub = self._subscription(payment_status=payment_status, record_active=record_active)
        invoice = self._invoice(number=f'LP-APROB-{payment_status}-{record_active}')
        self._item(invoice, sub)
        return invoice, sub

    def test_linea_aprobable_devuelve_la_unica_linea_pendiente(self):
        invoice, sub = self._factura_de_una_linea('pending')

        linea = invoice.linea_aprobable

        self.assertIsNotNone(linea)
        self.assertEqual(linea['uuid'], str(sub.uuid))

    def test_linea_aprobable_es_none_si_la_unica_linea_esta_solicitada(self):
        invoice, _ = self._factura_de_una_linea('requested')
        self.assertIsNone(invoice.linea_aprobable)

    def test_linea_aprobable_es_none_si_la_unica_linea_esta_pagada(self):
        invoice, _ = self._factura_de_una_linea('paid')
        self.assertIsNone(invoice.linea_aprobable)

    def test_linea_aprobable_es_none_si_la_unica_linea_esta_cancelada(self):
        # Baja lógica con el pago todavía en `pending`: `aprobable` exige
        # `record_active`, así que la propiedad no ofrece el botón sobre una
        # suscripción anulada (el listado de suscripciones tampoco).
        invoice, _ = self._factura_de_una_linea('pending', record_active=False)
        self.assertIsNone(invoice.linea_aprobable)

    def test_linea_aprobable_es_none_con_dos_lineas_aunque_una_este_pendiente(self):
        # Con dos o más líneas manda el desglose: la acción de fila sería ambigua.
        sub_pending = self._subscription(payment_status='pending')
        sub_paid = self._subscription(payment_status='paid')
        invoice = self._invoice(number='LP-APROB-DOS')
        self._item(invoice, sub_pending)
        self._item(invoice, sub_paid)
        self.assertIsNone(invoice.linea_aprobable)

    def test_linea_aprobable_es_none_sin_lineas(self):
        invoice = self._invoice(number='LP-APROB-CERO')
        self.assertIsNone(invoice.linea_aprobable)


class LinePaymentsListTests(_LinePaymentsBase):
    """El listado muestra el desglose y el link de aprobación gateado."""

    def setUp(self):
        self.url = reverse('commercial:factura_list')
        self.client.force_login(self.admin)

    def _factura_lote(self, *, number='LP-LOTE-1', pdf_status=Invoice.PdfStatus.READY, **kwargs):
        sub_paid = self._subscription(payment_status='paid')
        sub_pending = self._subscription(payment_status='pending')
        invoice = self._invoice(
            number=number,
            pdf=kwargs.pop('pdf', 'factura/lote.pdf'),
            pdf_status=pdf_status,
            **kwargs,
        )
        self._item(invoice, sub_paid, importe=Decimal('10.00'))
        self._item(invoice, sub_pending, importe=Decimal('20.00'))
        return invoice, sub_pending

    def test_muestra_el_resumen_de_lineas_cobradas(self):
        self._factura_lote()
        html = self.client.get(self.url).content.decode()
        self.assertIn('1/2 cobradas', html)

    def test_despliega_cada_linea_con_su_estado(self):
        self._factura_lote()
        html = self.client.get(self.url).content.decode()
        self.assertIn('por cobrar', html)
        self.assertIn('cobrada', html)
        self.assertIn(self.service.title, html)

    def test_ofrece_aprobar_pago_de_la_linea_pendiente(self):
        _, sub_pending = self._factura_lote()
        html = self.client.get(self.url).content.decode()
        self.assertIn(reverse('commercial:suscripcion_approve', args=[sub_pending.uuid]), html)

    def test_sin_pdf_listo_no_ofrece_aprobar_pago(self):
        _, sub_pending = self._factura_lote(pdf='', pdf_status=Invoice.PdfStatus.PENDING)
        html = self.client.get(self.url).content.decode()
        self.assertNotIn(reverse('commercial:suscripcion_approve', args=[sub_pending.uuid]), html)

    def test_factura_anulada_no_ofrece_aprobar_pago(self):
        _, sub_pending = self._factura_lote(number='LP-ANULADA', is_cancelled=True)
        html = self.client.get(self.url).content.decode()
        self.assertNotIn(reverse('commercial:suscripcion_approve', args=[sub_pending.uuid]), html)

    def test_linea_ya_cobrada_no_ofrece_aprobar_pago(self):
        sub_paid = self._subscription(payment_status='paid')
        invoice = self._invoice(number='LP-COBRADA')
        self._item(invoice, sub_paid)
        html = self.client.get(self.url).content.decode()
        self.assertNotIn(reverse('commercial:suscripcion_approve', args=[sub_paid.uuid]), html)

    def test_una_linea_solicitada_no_ofrece_aprobar_pago(self):
        # `ApproveSubscriptionView` rechaza todo lo que no esté `pending`
        # (`subscriptions.py:190-193`), y el listado de suscripciones tampoco
        # ofrece "Aprobar Pago" en `requested`: ofrecerlo acá sería un enlace
        # muerto que contradice la otra pantalla. En una factura de una línea no
        # hay desglose (manda el botón de Acciones), y con la línea en
        # `requested` ese botón no se ofrece.
        sub_requested = self._subscription(payment_status='requested')
        invoice = self._invoice(number='LP-SOLICITADA')
        self._item(invoice, sub_requested)
        html = self.client.get(self.url).content.decode()
        self.assertNotIn('cobradas', html)
        self.assertNotIn('<details', html)
        self.assertNotIn(reverse('commercial:suscripcion_approve', args=[sub_requested.uuid]), html)

    def test_no_staff_no_ve_el_link_pero_si_el_desglose(self):
        _, sub_pending = self._factura_lote(number='LP-NOSTAFF')
        outsider = self._grant_view_invoice(make_user('linenostaff'))
        self.client.force_login(outsider)
        html = self.client.get(self.url).content.decode()
        self.assertIn('1/2 cobradas', html)
        self.assertNotIn(reverse('commercial:suscripcion_approve', args=[sub_pending.uuid]), html)

    def _factura_de_una_linea(self, *, number='LP-UNA-1', pdf_status=Invoice.PdfStatus.READY):
        sub = self._subscription(payment_status='pending')
        invoice = self._invoice(number=number, pdf='factura/una.pdf', pdf_status=pdf_status)
        self._item(invoice, sub)
        return invoice, sub

    def test_factura_de_una_linea_no_despliega_el_desglose(self):
        # Con una sola línea el desglose repetiría el servicio de la columna
        # Servicio(s): en su lugar el link va como botón de Acciones.
        self._factura_de_una_linea()
        html = self.client.get(self.url).content.decode()
        self.assertNotIn('cobradas', html)
        self.assertNotIn('<details', html)

    def test_factura_de_una_linea_ofrece_aprobar_pago_en_las_acciones(self):
        _, sub = self._factura_de_una_linea(number='LP-UNA-ACCIONES')
        html = self.client.get(self.url).content.decode()
        url = reverse('commercial:suscripcion_approve', args=[sub.uuid])
        self.assertEqual(html.count(url), 1)
        self.assertIn('ti-circle-check', html)

    def test_factura_de_varias_lineas_no_duplica_el_aprobar_pago(self):
        # Con dos líneas el único link vive en el desglose; Acciones no repite.
        _, sub_pending = self._factura_lote(number='LP-VARIAS-DUP')
        html = self.client.get(self.url).content.decode()
        url = reverse('commercial:suscripcion_approve', args=[sub_pending.uuid])
        self.assertEqual(html.count(url), 1)


class LinePaymentsEndpointTests(_LinePaymentsBase):
    """`ajax_invoice_status` rinde la misma celda: mismo desglose y mismo gate."""

    def setUp(self):
        self.url = reverse('commercial:ajax_invoice_status')
        self.client.force_login(self.admin)

    def _status_html(self, invoice):
        response = self.client.get(self.url, {'uuids': str(invoice.uuid)})
        self.assertEqual(response.status_code, 200)
        return response.json()['rows'][0]['status_html']

    def test_el_endpoint_devuelve_el_mismo_desglose_y_el_link(self):
        sub_pending = self._subscription(payment_status='pending')
        sub_paid = self._subscription(payment_status='paid')
        invoice = self._invoice(number='LP-AJAX')
        self._item(invoice, sub_pending)
        self._item(invoice, sub_paid)

        status_html = self._status_html(invoice)

        self.assertIn('1/2 cobradas', status_html)
        self.assertIn(
            reverse('commercial:suscripcion_approve', args=[sub_pending.uuid]), status_html
        )

    def test_el_endpoint_respeta_el_gate_sin_pdf(self):
        sub_pending = self._subscription(payment_status='pending')
        invoice = self._invoice(
            number='LP-AJAX-NOPDF', pdf='', pdf_status=Invoice.PdfStatus.PENDING
        )
        self._item(invoice, sub_pending)

        status_html = self._status_html(invoice)

        self.assertNotIn(
            reverse('commercial:suscripcion_approve', args=[sub_pending.uuid]), status_html
        )


class NoQueryPerLineTests(_LinePaymentsBase):
    """Dos facturas de dos líneas no suman una consulta por línea.

    El desglose lee `subscription.payment_status`, `record_active` y
    `service.title` de cada línea, y `items` no viene prefetcheado por defecto.
    Sin el `Prefetch('items', select_related('subscription__service'))` de la
    queryset del listado, cada línea pagaría su propia consulta a
    suscripción/servicio (el N+1 que el diseño evita).
    """

    def _lote(self):
        # Dos facturas, cada una con dos líneas de dos suscripciones distintas.
        for n in range(2):
            invoice = self._invoice(number=f'LP-N1-{n}')
            for _ in range(2):
                sub = self._subscription(payment_status='pending')
                self._item(invoice, sub)

    def test_la_queryset_del_listado_resuelve_las_lineas_con_dos_consultas(self):
        self._lote()
        # Número correcto verificado: 1 consulta para las facturas (con las
        # anotaciones de `with_display_status`) + 1 del `Prefetch` de líneas con
        # `select_related` a suscripción y servicio. Acceder a `line_payments`
        # no agrega consultas: todo sale del prefetch.
        with self.assertNumQueries(2):
            invoices = list(InvoiceListView().get_queryset())
            rendered = [line for invoice in invoices for line in invoice.line_payments]
        self.assertEqual(len(rendered), 4)

    def test_el_listado_no_crece_en_consultas_por_linea(self):
        # Refuerzo end-to-end: mismas dos facturas, primero con una línea y
        # luego con dos. Si hubiera consulta por línea, el segundo GET sumaría.
        invoices = []
        for n in range(2):
            invoice = self._invoice(number=f'LP-N2-{n}')
            self._item(invoice, self._subscription(payment_status='pending'))
            invoices.append(invoice)
        self.client.force_login(self.admin)

        with CaptureQueriesContext(connection) as una_linea:
            self.assertEqual(self.client.get(reverse('commercial:factura_list')).status_code, 200)

        for invoice in invoices:
            self._item(invoice, self._subscription(payment_status='pending'))
        with CaptureQueriesContext(connection) as dos_lineas:
            self.assertEqual(self.client.get(reverse('commercial:factura_list')).status_code, 200)

        self.assertEqual(len(una_linea.captured_queries), len(dos_lineas.captured_queries))
