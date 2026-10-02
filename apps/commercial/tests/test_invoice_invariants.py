"""Invariantes de documentos: lo pagado tiene que estar respaldado por un papel.

Dos reglas que el código no escribía y que la base de desarrollo ya tenía
incumplidas:

- **Suscripción `paid` ⇒ al menos un certificado con PDF.** La acción masiva de
  suscripciones permite `payment_status='paid'` en su allow-list y lo aplicaba
  sin mirar documentos, así que una suscripción podía quedar pagada sin
  certificado. El camino normal para aprobar el pago
  (`ApproveSubscriptionView`) sube el certificado antes de marcar `paid`, y por
  eso estos tests también lo fijan para que nadie lo rompa.
- **Factura pagada ⇒ PDF disponible.** El PDF se genera en una tarea Huey
  asíncrona que puede fallar o no correr (en desarrollo el worker no siempre
  está vivo), así que la factura pagada sin PDF no se puede volver imposible:
  lo que tiene que existir es que el estado se vea en el listado y que haya una
  vía de reparación. Por eso el listado marca "Pagada sin PDF" y la factura se
  puede volver a encolar para renderizar el PDF sin reenviar el correo.
"""

import json
import re
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.commercial.models import (
    Certificate,
    Invoice,
    InvoiceItem,
    Service,
    ServiceSubscription,
)
from apps.commercial.tests.factories import make_user, natural_customer
from apps.core.models import SiteConfiguration


def _make_superuser(username):
    return User.objects.create_superuser(
        username,
        f'{username}@example.com',
        'pass',
        first_name='Admin',
        last_name='Super',
    )


def _suscripcion(customer, service, payment_status='requested'):
    return ServiceSubscription.objects.create(
        customer=customer,
        service=service,
        quantity=10,
        payment_status=payment_status,
    )


def _certificado(subscription, con_pdf=True):
    pdf = SimpleUploadedFile('cert.pdf', b'%PDF-1.4 test', 'application/pdf') if con_pdf else ''
    return Certificate.objects.create(subscription=subscription, pdf=pdf)


def _factura(
    customer, subscription, number, pdf_status=Invoice.PdfStatus.PENDING, is_cancelled=False
):
    invoice = Invoice.objects.create(
        subscription=subscription,
        customer=customer,
        number=number,
        amount=Decimal('450.00'),
        pdf_status=pdf_status,
        is_cancelled=is_cancelled,
    )
    InvoiceItem.objects.create(
        invoice=invoice,
        subscription=subscription,
        descripcion='Pronóstico diario',
        cantidad=Decimal('10'),
        precio=Decimal('45.00'),
        importe=Decimal('450.00'),
    )
    return invoice


class _CasoBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        cls.admin = _make_superuser('invadmin')
        cls.customer = natural_customer(
            make_user('invcust', first_name='Ana', last_name='Norte'),
        )
        cls.service = Service.objects.create(
            user=cls.admin,
            title='Pronóstico diario',
            summary='Pronóstico puntual',
            service_type='commercial',
            service_category='pronostico',
            code='INV01',
            price=Decimal('45.00'),
        )

    def _sub(self, payment_status='requested'):
        return _suscripcion(self.customer, self.service, payment_status)


class AccionMasivaCertificadoTests(_CasoBase):
    """`paid` no se alcanza por la acción masiva sin certificado con PDF."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sin_certificado = _suscripcion(cls.customer, cls.service, 'requested')
        cls.con_certificado = _suscripcion(cls.customer, cls.service, 'requested')
        cls.certificado = _certificado(cls.con_certificado)
        cls.url = reverse('commercial:suscripcion_bulk')

    def setUp(self):
        self.client.force_login(self.admin)
        ct = ContentType.objects.get_for_model(ServiceSubscription)
        self.admin.user_permissions.add(ct.permission_set.get(codename='change_subscription'))

    def _update(self, subs, value, field='payment_status'):
        data = {
            'action': 'update',
            'uuids': [str(sub.uuid) for sub in subs],
            'field': field,
            'value': value,
        }
        return self.client.post(self.url, json.dumps(data), content_type='application/json')

    def test_rechaza_paid_en_una_suscripcion_sin_certificado(self):
        response = self._update([self.sin_certificado], 'paid')

        self.assertEqual(response.status_code, 400)
        cuerpo = response.json()
        self.assertEqual(cuerpo['processed'], 0)
        self.assertIn('certificado', cuerpo['error'].lower())
        self.sin_certificado.refresh_from_db()
        self.assertEqual(self.sin_certificado.payment_status, 'requested')

    def test_rechaza_paid_si_el_certificado_no_tiene_pdf(self):
        sub = self._sub('requested')
        cert = _certificado(sub, con_pdf=False)
        self.assertEqual(cert.pdf.name, '', 'precondición: certificado sin archivo')

        response = self._update([sub], 'paid')

        self.assertEqual(response.status_code, 400)
        sub.refresh_from_db()
        self.assertEqual(sub.payment_status, 'requested')

    def test_rechaza_paid_si_el_certificado_esta_dado_de_baja(self):
        sub = self._sub('requested')
        _certificado(sub).delete()

        response = self._update([sub], 'paid')

        self.assertEqual(response.status_code, 400)
        sub.refresh_from_db()
        self.assertEqual(sub.payment_status, 'requested')

    def test_acepta_paid_cuando_ya_hay_certificado(self):
        response = self._update([self.con_certificado], 'paid')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['processed'], 1)
        self.con_certificado.refresh_from_db()
        self.assertEqual(self.con_certificado.payment_status, 'paid')

    def test_una_seleccion_mixta_no_aplica_nada(self):
        """O se cumple para todas, o no se toca ninguna: nada de estados a medias."""
        response = self._update([self.con_certificado, self.sin_certificado], 'paid')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['processed'], 0)
        self.con_certificado.refresh_from_db()
        self.sin_certificado.refresh_from_db()
        self.assertEqual(self.con_certificado.payment_status, 'requested')
        self.assertEqual(self.sin_certificado.payment_status, 'requested')

    def test_requested_y_pending_siguen_funcionando(self):
        response = self._update([self.sin_certificado], 'pending')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['processed'], 1)
        self.sin_certificado.refresh_from_db()
        self.assertEqual(self.sin_certificado.payment_status, 'pending')

        sub = self._sub('requested')
        respuesta = self._update([sub], 'requested')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['processed'], 1)

    def test_el_campo_no_permitido_sigue_siendo_rechazado_primero(self):
        response = self._update(
            [self.sin_certificado],
            str(self.customer.pk),
            field='customer',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('allow-list', response.json()['error'])


class AprobarPagoMantieneLaInvarianteTests(_CasoBase):
    """El camino principal ya era correcto: aprobar sube el certificado."""

    def setUp(self):
        self.client.force_login(self.admin)

    def test_aprobar_pago_deja_certificado_y_estado_pagado(self):
        sub = self._sub('pending')
        url = reverse('commercial:suscripcion_approve', args=[sub.uuid])
        pdf = SimpleUploadedFile('certificado.pdf', b'%PDF-1.4', 'application/pdf')

        with patch('apps.commercial.views.subscriptions.enviar_correo_certificado'):
            self.client.post(url, {'pdf': pdf}, follow=True)

        sub.refresh_from_db()
        self.assertEqual(sub.payment_status, 'paid')
        self.assertEqual(
            Certificate.objects.filter(subscription=sub, record_active=True).count(),
            1,
            'la invariante depende de que aprobar el pago deje el certificado',
        )

    def test_aprobar_pago_de_una_suscripcion_no_pendiente_no_crea_certificado(self):
        sub = self._sub('requested')
        url = reverse('commercial:suscripcion_approve', args=[sub.uuid])
        pdf = SimpleUploadedFile('certificado.pdf', b'%PDF-1.4', 'application/pdf')

        self.client.post(url, {'pdf': pdf}, follow=True)

        sub.refresh_from_db()
        self.assertEqual(sub.payment_status, 'requested')
        self.assertEqual(Certificate.objects.filter(subscription=sub).count(), 0)


class FacturaPagadaSinPdfTests(_CasoBase):
    """El PDF es asíncrono: el estado tiene que verse y poder repararse."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sub_paid = _suscripcion(cls.customer, cls.service, 'paid')
        cls.sub_pendiente = _suscripcion(cls.customer, cls.service, 'pending')
        cls.factura_pagada = _factura(
            cls.customer,
            cls.sub_paid,
            '2026-9001',
            pdf_status=Invoice.PdfStatus.FAILED,
        )
        cls.factura_pagada.pdf_error = 'sin Pango'
        cls.factura_pagada.save(update_fields=['pdf_error'])
        cls.factura_pendiente = _factura(cls.customer, cls.sub_pendiente, '2026-9002')

    def setUp(self):
        self.client.force_login(self.admin)
        self.url_list = reverse('commercial:factura_list')

    def test_el_listado_avisa_cuando_la_factura_esta_pagada_sin_pdf(self):
        html = self.client.get(self.url_list).content.decode()

        self.assertIn('2026-9001', html)
        self.assertIn('Pagada sin PDF', html)

    def test_solo_avisa_de_la_factura_pagada_sin_pdf(self):
        """La factura pendiente sin PDF es otro problema: no va con este aviso."""
        html = self.client.get(self.url_list).content.decode()

        self.assertEqual(html.count('Pagada sin PDF'), 1)

    def test_con_el_pdf_listo_deja_de_avisar(self):
        self.factura_pagada.pdf = 'factura/invoice/2026-9001.pdf'
        self.factura_pagada.pdf_status = Invoice.PdfStatus.READY
        self.factura_pagada.save(update_fields=['pdf', 'pdf_status'])

        html = self.client.get(self.url_list).content.decode()

        self.assertNotIn('Pagada sin PDF', html)


class RepararPdfDeFacturaTests(_CasoBase):
    """La reparación: reencolar sólo el render del PDF, sin reenviar el correo."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sub = _suscripcion(cls.customer, cls.service, 'pending')
        cls.factura = _factura(
            cls.customer,
            cls.sub,
            '2026-9003',
            pdf_status=Invoice.PdfStatus.FAILED,
        )

    def setUp(self):
        self.client.force_login(self.admin)
        self.url_list = reverse('commercial:factura_list')

    def test_el_listado_ofrece_la_reparacion(self):
        html = self.client.get(self.url_list).content.decode()

        self.assertIn(reverse('commercial:factura_retry_pdf', args=[self.factura.uuid]), html)

    def test_reintentar_reencola_solo_el_pdf(self):
        url = reverse('commercial:factura_retry_pdf', args=[self.factura.uuid])

        with patch('apps.commercial.views.invoices.generate_invoice_pdf_and_email_task') as tarea:
            self.client.post(url, follow=True)

        self.assertEqual(tarea.call_count, 1)
        args, kwargs = tarea.call_args
        self.assertEqual(args[0], str(self.factura.uuid))
        self.assertEqual(
            kwargs.get('solo_paso'),
            'pdf',
            'reenviar el correo no es parte de la reparación del PDF',
        )

    def test_reintentar_una_factura_con_pdf_listo_no_hace_nada(self):
        self.factura.pdf = 'factura/invoice/2026-9003.pdf'
        self.factura.pdf_status = Invoice.PdfStatus.READY
        self.factura.save(update_fields=['pdf', 'pdf_status'])
        url = reverse('commercial:factura_retry_pdf', args=[self.factura.uuid])

        with patch('apps.commercial.views.invoices.generate_invoice_pdf_and_email_task') as tarea:
            self.client.post(url, follow=True)

        tarea.assert_not_called()

    def test_reintentar_una_factura_anulada_no_hace_nada(self):
        self.factura.is_cancelled = True
        self.factura.save(update_fields=['is_cancelled'])
        url = reverse('commercial:factura_retry_pdf', args=[self.factura.uuid])

        with patch('apps.commercial.views.invoices.generate_invoice_pdf_and_email_task') as tarea:
            self.client.post(url, follow=True)

        tarea.assert_not_called()


class FacturaAnuladaAccionesTests(_CasoBase):
    """Acciones coherentes para facturas anuladas."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sub = _suscripcion(cls.customer, cls.service, 'pending')
        cls.factura_anulada = _factura(
            cls.customer,
            cls.sub,
            '2026-9005',
            is_cancelled=True,
            pdf_status=Invoice.PdfStatus.READY,
        )
        cls.factura_anulada.pdf = 'factura/invoice/2026-9005.pdf'
        cls.factura_anulada.save(update_fields=['pdf'])

    def setUp(self):
        self.client.force_login(self.admin)
        self.url_list = reverse('commercial:factura_list')

    def _boton_de_accion(self, html, uuid, action):
        """¿Está el botón `action` de esta factura, y no el de otra fila?

        "Anular" y "Eliminar" no son enlaces ni forms con la URL real: el
        template pone un UUID placeholder y el JS lo reemplaza en el click. Por
        eso buscar el path no sirve (nunca aparece) y hay que atar el marcador
        al `data-uuid` de la fila que nos interesa.
        """
        patron = rf'data-action="{action}"[^>]*?data-uuid="{uuid}"'
        return re.search(patron, html, re.DOTALL) is not None

    def test_factura_anulada_no_muestra_editar_ni_reenviar_ni_cancelar_ni_reintentar(self):
        """Una factura anulada no ofrece acciones de vida, sólo las de consulta.

        Las aserciones van sobre la URL **resuelta** o sobre el marcador del
        botón atado a su UUID, nunca sobre el nombre de la ruta: `{% url %}`
        renderiza el path y el nombre (`factura_cancel`) jamás aparece en el
        HTML, así que buscarlo pasa siempre. Un test que pasa sin comprobar
        nada es peor que no tener test.
        """
        html = self.client.get(self.url_list).content.decode()
        uuid = str(self.factura_anulada.uuid)

        self.assertIn('2026-9005', html)

        # Acciones de vida con URL resuelta.
        self.assertNotIn(reverse('commercial:factura_resend_email', args=[uuid]), html)
        self.assertNotIn(reverse('commercial:factura_retry_pdf', args=[uuid]), html)

        # Acciones de vida con URL construida por JS.
        self.assertFalse(self._boton_de_accion(html, uuid, 'anular'))

        # Y también sobre el texto que el operador ve en pantalla. Ojo con
        # "Anular factura": ese literal vive en el JS del modal y está siempre
        # en la página, así que no dice nada sobre el botón de esta fila; para
        # ese caso el marcador `data-action` atado al UUID sí es concluyente.
        self.assertNotIn('Reenviar correo', html)
        self.assertNotIn('Generar PDF', html)
        self.assertNotIn('Editar', html)
        self.assertNotIn('Facturar', html)

    def test_factura_anulada_muestra_pdf_y_borrado_para_superusuario(self):
        """Con el PDF listo, la anulada conserva descarga y borrado definitivo."""
        html = self.client.get(self.url_list).content.decode()
        uuid = str(self.factura_anulada.uuid)

        self.assertIn('2026-9005', html)
        self.assertIn(reverse('commercial:factura_download', args=[uuid]), html)
        self.assertIn('Ver Factura', html)
        self.assertTrue(self._boton_de_accion(html, uuid, 'eliminar'))

    def test_factura_viva_no_ofrece_borrado_definitivo(self):
        """El borrado definitivo es sólo de anuladas: es la contraejecuta."""
        factura = _factura(self.customer, self.sub, '2026-9007')
        factura.pdf = 'factura/invoice/2026-9007.pdf'
        factura.pdf_status = Invoice.PdfStatus.READY
        factura.save(update_fields=['pdf', 'pdf_status'])
        html = self.client.get(self.url_list).content.decode()

        self.assertIn('2026-9007', html)
        self.assertFalse(self._boton_de_accion(html, str(factura.uuid), 'eliminar'))
        self.assertTrue(self._boton_de_accion(html, str(factura.uuid), 'anular'))

    def test_factura_anulada_sin_pdf_no_ofrece_descarga_nada(self):
        """Sin PDF listo tampoco hay descarga: el botón mentiría."""
        factura = _factura(
            self.customer, self.sub, '2026-9006', is_cancelled=True, pdf_status='failed'
        )
        html = self.client.get(self.url_list).content.decode()

        self.assertIn('2026-9006', html)
        self.assertNotIn(reverse('commercial:factura_download', args=[str(factura.uuid)]), html)
        # El borrado definitivo sigue disponible: es la vía de limpieza.
        self.assertTrue(self._boton_de_accion(html, str(factura.uuid), 'eliminar'))
