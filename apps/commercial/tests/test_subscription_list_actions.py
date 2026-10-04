"""Coherencia de las acciones del listado de suscripciones.

Dos invariantes de UI que no se pueden verificar en la vista sino en el HTML
renderizado:

- Una suscripción anulada (`record_active=False`) no debe ofrecer acciones de
  vida: ni facturar, ni editar, ni aprobar pago, ni regenerar factura. Ya no
  hay nada que cobrar y el botón apunta a un flujo que no puede terminar.
- Ver y descargar sólo tienen sentido si el PDF existe de verdad. La vista
  anota el UUID de la última factura no anulada, pero que exista el UUID no
  significa que el render haya terminado: una factura con `pdf_status='failed'`
  rompía el botón de descarga.
"""

from django.contrib.auth.models import User
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


class SubscriptionListActionsTests(TestCase):
    """Acciones del listado de suscripciones según el estado de la fila."""

    @classmethod
    def setUpTestData(cls):
        # El `CheckUserProfileMiddleware` manda a /accounts/profile/update/ a
        # cualquier usuario sin nombres, así que el staff de prueba los tiene.
        cls.staff = User.objects.create_superuser(
            'staff_acciones', 'staff@acciones.test', 'pw', first_name='Sta', last_name='Ff'
        )
        cls.customer = natural_customer(username='cliente_acciones')
        cls.service = Service.objects.create(
            user=cls.staff,
            title='Servicio de prueba',
            summary='s',
            service_type=Service.COMMERCIAL,
            price=100,
            service_category='agrometeo',
            code='SRV-ACC',
        )

    def setUp(self):
        self.client.force_login(self.staff)

    def _subscription(self, payment_status, record_active=True):
        return ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.service,
            start_date=timezone.now().date(),
            payment_status=payment_status,
            quantity=1,
            record_active=record_active,
        )

    def _invoice(self, subscription, pdf='', pdf_status='pending'):
        invoice = Invoice.objects.create(
            customer=self.customer,
            subscription=subscription,
            amount=100,
            number=f'ACC-{Invoice.objects.count() + 1}',
            pdf=pdf,
            pdf_status=pdf_status,
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            subscription=subscription,
            codigo='SRV-ACC',
            descripcion='Servicio de prueba',
            cantidad=1,
            unidad_medida='MES',
            precio=100,
            importe=100,
        )
        return invoice

    def _render(self, subscription):
        response = self.client.get(reverse('commercial:suscripcion_list'))
        self.assertEqual(response.status_code, 200)
        rows = response.context['objects']
        row = next(r for r in rows if r.pk == subscription.pk)
        return row, response.content.decode()

    # ---------------------------------------------------------------- T5

    def test_subscription_anulada_solicitada_no_ofrece_facturar_ni_editar(self):
        """El caso que reportó el operador: anular no debe dejar botones vivos."""
        subscription = self._subscription('requested', record_active=False)

        _, html = self._render(subscription)

        self.assertNotIn('title="Facturar"', html)
        self.assertNotIn('title="Editar"', html)
        # Y tampoco la URL de facturación, que es la otra mitad del mismo botón.
        self.assertNotIn(reverse('commercial:factura_create'), html)

    def test_subscription_anulada_pendiente_no_ofrece_aprobar_pago(self):
        subscription = self._subscription('pending', record_active=False)
        self._invoice(subscription, pdf='facturas/ok.pdf', pdf_status='ready')

        _, html = self._render(subscription)

        self.assertNotIn('title="Aprobar Pago"', html)
        self.assertNotIn(reverse('commercial:suscripcion_approve', args=[subscription.uuid]), html)

    def test_subscription_anulada_no_ofrece_regenerar_factura(self):
        """Regenerar sobre una suscripción anulada no tiene nada que reemplazar."""
        subscription = self._subscription('pending', record_active=False)
        self._invoice(subscription, pdf='facturas/ok.pdf', pdf_status='ready')

        _, html = self._render(subscription)

        self.assertNotIn(reverse('commercial:factura_regenerate', args=[subscription.uuid]), html)

    def test_subscription_anulada_no_ofrece_anular_de_nuevo(self):
        """El botón de anular sólo va con `record_active`, pero el badge tampoco."""
        subscription = self._subscription('requested', record_active=False)

        _, html = self._render(subscription)

        self.assertNotIn('title="Anular suscripción"', html)

    def test_solicitada_activa_sigue_ofreciendo_facturar_y_editar(self):
        """El caso válido no se rompe: sigue habiendo botón de facturar."""
        subscription = self._subscription('requested')

        _, html = self._render(subscription)

        self.assertIn('title="Facturar"', html)
        self.assertIn('title="Editar"', html)

    # ---------------------------------------------------------------- T5

    def test_no_ofrece_descargar_factura_cuyo_pdf_fallo(self):
        """El UUID existe pero el render no terminó: no hay nada que descargar."""
        subscription = self._subscription('pending')
        self._invoice(subscription, pdf='', pdf_status='failed')

        row, html = self._render(subscription)

        self.assertTrue(row.latest_invoice_uuid, 'la vista debe seguir anotando la factura')
        download_url = reverse('commercial:factura_download', args=[row.latest_invoice_uuid])
        self.assertNotIn(download_url, html)

    def test_no_ofrece_descargar_factura_sin_pdf_pero_con_archivo_vacio(self):
        """`pdf_ready` exige archivo Y estado: un pdf vacío no alcanza."""
        subscription = self._subscription('pending')
        self._invoice(subscription, pdf='', pdf_status='ready')

        _, html = self._render(subscription)

        self.assertNotIn('title="Descargar Factura"', html)

    def test_si_ofrece_descargar_cuando_el_pdf_esta_listo(self):
        subscription = self._subscription('pending')
        self._invoice(subscription, pdf='facturas/ok.pdf', pdf_status='ready')

        _, html = self._render(subscription)

        self.assertIn('title="Descargar Factura"', html)
        self.assertIn('title="Ver Factura"', html)

    # ---------------------------------------------------------------- T6

    def test_celda_de_acciones_usa_flex_con_gap_para_movil(self):
        """
        Espaciado de T6: en móvil los botones se amontonan sin un contenedor
        flex con gap. El contrato es que la celda de acciones use el layout
        `d-flex flex-wrap justify-content-end gap-2`.
        """
        subscription = self._subscription('requested')

        _, html = self._render(subscription)

        self.assertIn('d-flex flex-wrap justify-content-end gap-2', html)


class LatestInvoicePdfReadyAnnotationTests(TestCase):
    """La anotación SQL y `Invoice.pdf_ready` no pueden divergir.

    El listado necesita saber si el PDF de la última factura está listo sin
    disparar una consulta por fila, así que replica la condición de
    `Invoice.pdf_ready` en SQL. Replicar una condición en dos lugares es la vía
    clásica para que dejen de coincidir sin que nada falle, así que este test
    las ata: cualquier caso que disagrees es un bug, no una diferencia
    aceptable.
    """

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_superuser(
            'staff_pdfready', 'staff@pdfready.test', 'pw', first_name='Sta', last_name='Ff'
        )
        cls.customer = natural_customer(username='cliente_pdfready')
        cls.service = Service.objects.create(
            user=cls.staff,
            title='Servicio pdf',
            summary='s',
            service_type=Service.COMMERCIAL,
            price=100,
            service_category='agrometeo',
            code='SRV-PDF',
        )

    def setUp(self):
        self.client.force_login(self.staff)

    def test_la_anotacion_coincide_con_pdf_ready_en_las_cuatro_combinaciones(self):
        combinaciones = [
            ('pendiente', 'facturas/x.pdf', False),
            ('failed', 'facturas/x.pdf', False),
            ('ready', '', False),
            ('ready', 'facturas/x.pdf', True),
        ]
        for pdf_status, pdf, esperado in combinaciones:
            with self.subTest(pdf_status=pdf_status, pdf=pdf):
                subscription = ServiceSubscription.objects.create(
                    customer=self.customer,
                    service=self.service,
                    start_date=timezone.now().date(),
                    payment_status='pending',
                    quantity=1,
                )
                invoice = Invoice.objects.create(
                    customer=self.customer,
                    subscription=subscription,
                    amount=100,
                    number=f'PDF-{Invoice.objects.count() + 1}',
                    pdf=pdf,
                    pdf_status=pdf_status,
                )
                InvoiceItem.objects.create(
                    invoice=invoice,
                    subscription=subscription,
                    codigo='SRV-PDF',
                    descripcion='Servicio pdf',
                    cantidad=1,
                    unidad_medida='MES',
                    precio=100,
                    importe=100,
                )

                # La anotación sale de la vista real, no de una copia local de
                # la condición: si el test replicara el Case/When del código
                # estaría comprobando que una expresión es igual a sí misma.
                fila = self._fila_de_la_vista(subscription)

                self.assertEqual(bool(fila.latest_invoice_pdf_ready), invoice.pdf_ready)
                self.assertEqual(bool(fila.latest_invoice_pdf_ready), esperado)

    def _fila_de_la_vista(self, subscription):
        response = self.client.get(reverse('commercial:suscripcion_list'))
        self.assertEqual(response.status_code, 200)
        return next(r for r in response.context['objects'] if r.pk == subscription.pk)

    def test_la_anotacion_ignora_las_facturas_anuladas(self):
        """La factura anulada no cuenta: la suscripción queda sin PDF listo."""
        subscription = ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.service,
            start_date=timezone.now().date(),
            payment_status='pending',
            quantity=1,
        )
        invoice = Invoice.objects.create(
            customer=self.customer,
            subscription=subscription,
            amount=100,
            number='PDF-ANULADA',
            pdf='facturas/x.pdf',
            pdf_status='ready',
            is_cancelled=True,
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            subscription=subscription,
            codigo='SRV-PDF',
            descripcion='Servicio pdf',
            cantidad=1,
            unidad_medida='MES',
            precio=100,
            importe=100,
        )

        response = self.client.get(reverse('commercial:suscripcion_list'))
        fila = next(r for r in response.context['objects'] if r.pk == subscription.pk)

        self.assertFalse(fila.latest_invoice_pdf_ready)
        self.assertNotIn('title="Descargar Factura"', response.content.decode())
