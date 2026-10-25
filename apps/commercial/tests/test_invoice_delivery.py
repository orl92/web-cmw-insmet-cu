"""Entrega de la factura: PDF y correo como pasos con estado propio.

Estos tests fijan el comportamiento que reportaba el operador:

- el PDF se renderiza una vez y no se vuelve a renderizar cuando lo que
  falla es el correo;
- los botones de ver/descargar existen solo cuando el PDF quedó `ready`;
- reintentar una tarea actualiza su fila en el log, no abre una nueva;
- la tabla de tareas dice de qué cliente es cada una;
- una factura borrada con la tarea en la cola no genera reintentos para siempre.

Y lo que el cliente ve al abrir ese correo:

- el asunto lleva el nombre visible del cliente (no la palabra `None`);
- el QR de pago se muestra en el cuerpo además de viajar adjunto;
- «Ver en línea» apunta a una página que el cliente sí puede abrir.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles import finders
from django.core import mail
from django.template.loader import render_to_string
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.commercial.models import Invoice, InvoiceItem, Service, ServiceSubscription
from apps.commercial.tests.factories import (
    juridica_customer,
    natural_customer,
    next_nit,
    next_reeup,
)
from apps.core.models import SiteConfiguration, TaskExecutionLog
from config.huey import huey

LOCMEM = 'django.core.mail.backends.locmem.EmailBackend'


class FacturaBase(TestCase):
    def setUp(self):
        # Estos tests encolan de verdad para que corran las señales, así que
        # dejan tareas en la cola. `test_runner` aísla el storage de Huey en
        # memoria por corrida, no por test: sin esto, las tareas sobreviven a
        # este test y `test_send_test_invoice` falla después al contar la cola.
        huey.flush()
        self.addCleanup(huey.flush)

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            'entrega',
            'entrega@ejemplo.cu',
            'pass',
            first_name='Ana',
            last_name='Entrega',
        )
        cls.customer = natural_customer(
            cls.user, address='Addr', phone='12345678', account='1234567890123456'
        )
        cls.invoice = Invoice.objects.create(
            customer=cls.customer,
            number='INV-ENTREGA',
            amount=Decimal('100.00'),
        )
        InvoiceItem.objects.create(
            invoice=cls.invoice,
            descripcion='Item',
            cantidad=1,
            precio=Decimal('100.00'),
        )

    def _render_ok(self):
        """Mock del render que **sí deja el archivo guardado**.

        Importa que guarde el archivo: `pdf_ready` exige estado `ready` *y*
        archivo, porque un estado sin archivo no es un PDF descargable. Un
        mock que solo devuelve bytes haría que la tarea re-renderizara en cada
        intento y el test probaría algo que el código real no hace.
        """

        def _render(invoice, *args, **kwargs):
            invoice.pdf.name = f'factura/invoice/{invoice.number}.pdf'
            invoice.save(update_fields=['pdf'])
            return b'%PDF-1.4'

        return patch(
            'apps.commercial.views.invoice_utils.generate_invoice_pdf_standalone',
            side_effect=_render,
        )

    def _correo_falla(self):
        """Simula un backend de correo que revienta."""
        mock = MagicMock()
        mock.send.side_effect = Exception('SMTP caido')
        return patch('apps.commercial.views.invoice_utils.EmailMessage', return_value=mock)

    def _correo_ok(self):
        return patch(
            'apps.commercial.views.invoice_utils.EmailMessage',
            return_value=MagicMock(),
        )


class EstadosDePdfTests(FacturaBase):
    def test_el_pdf_requiere_el_estado_ready_no_solo_el_archivo(self):
        """Un render a medias deja `pdf` poblado sin que haya un PDF usable."""
        self.invoice.pdf = 'factura/invoice/INV-ENTREGA.pdf'
        self.invoice.pdf_status = Invoice.PdfStatus.PENDING
        self.invoice.save()

        self.assertFalse(self.invoice.pdf_ready, 'un archivo sin estado ready no habilita nada')

        self.invoice.pdf_status = Invoice.PdfStatus.READY
        self.invoice.save()
        self.assertTrue(self.invoice.pdf_ready)

    def test_un_pdf_fallido_no_se_cuenta_como_listo(self):
        self.invoice.pdf = 'factura/invoice/INV-ENTREGA.pdf'
        self.invoice.pdf_status = Invoice.PdfStatus.FAILED
        self.invoice.pdf_error = 'sin Pango'
        self.invoice.save()

        self.assertFalse(self.invoice.pdf_ready)


class TareaIdempotenteTests(FacturaBase):
    """El motivo de que PDF y correo sean pasos separados y no una operación."""

    def test_el_fallo_del_correo_no_vuelve_a_renderizar_el_pdf(self):
        from apps.core.tasks import generate_invoice_pdf_and_email_task

        with (
            self._render_ok() as render,
            self._correo_falla(),
            self.assertRaises(RuntimeError),
        ):
            generate_invoice_pdf_and_email_task.call_local(str(self.invoice.uuid), 'http://t/')

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.pdf_status, Invoice.PdfStatus.READY)
        self.assertEqual(self.invoice.email_status, Invoice.EmailStatus.FAILED)
        self.assertIn('SMTP caido', self.invoice.email_error)
        self.assertEqual(render.call_count, 1, 'el PDF sí se generó en el primer intento')

        # Segundo intento, como el de Huey: el correo se reintenta, el PDF no.
        with (
            self._render_ok() as render,
            self._correo_falla(),
            self.assertRaises(RuntimeError),
        ):
            generate_invoice_pdf_and_email_task.call_local(str(self.invoice.uuid), 'http://t/')

        self.invoice.refresh_from_db()
        self.assertEqual(
            render.call_count,
            0,
            'el reintento no debe volver a renderizar un PDF que ya salió bien',
        )

    def test_no_reenvia_el_correo_si_ya_salio(self):
        from apps.core.tasks import generate_invoice_pdf_and_email_task

        with self._render_ok(), self._correo_ok():
            generate_invoice_pdf_and_email_task.call_local(str(self.invoice.uuid), 'http://t/')

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.email_status, Invoice.EmailStatus.SENT)

        with self._correo_falla() as correo:
            generate_invoice_pdf_and_email_task.call_local(str(self.invoice.uuid), 'http://t/')

        self.invoice.refresh_from_db()
        self.assertEqual(
            self.invoice.email_status,
            Invoice.EmailStatus.SENT,
            'una factura ya enviada no se reenvía sola en cada corrida',
        )
        self.assertEqual(correo.call_count, 0)

    def test_solo_paso_email_fuerza_el_correo_y_no_toca_el_pdf(self):
        from apps.core.tasks import generate_invoice_pdf_and_email_task

        with self._correo_falla(), self.assertRaises(RuntimeError):
            generate_invoice_pdf_and_email_task.call_local(str(self.invoice.uuid), 'http://t/')

        with self._render_ok() as render, self._correo_ok():
            generate_invoice_pdf_and_email_task.call_local(
                str(self.invoice.uuid), 'http://t/', solo_paso='email'
            )

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.email_status, Invoice.EmailStatus.SENT)
        self.assertEqual(render.call_count, 0, 'forzar el correo no genera el PDF')

    def test_solo_paso_pdf_no_envia_correo(self):
        from apps.core.tasks import generate_invoice_pdf_and_email_task

        with self._render_ok(), self._correo_ok() as correo:
            generate_invoice_pdf_and_email_task.call_local(
                str(self.invoice.uuid), 'http://t/', solo_paso='pdf'
            )

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.pdf_status, Invoice.PdfStatus.READY)
        self.assertEqual(
            self.invoice.email_status,
            Invoice.EmailStatus.PENDING,
            'reintentar el PDF no manda correo',
        )
        self.assertEqual(correo.call_count, 0)

    def test_una_factura_borrada_no_reintenta_para_siempre(self):
        """El ciclo de 144 tracebacks: la tarea reintentaba un `get()` que no
        podía funcionar nunca, porque la factura ya no existía."""
        from apps.core.tasks import generate_invoice_pdf_and_email_task

        uuid = str(self.invoice.uuid)
        self.invoice.hard_delete()

        # No debe levantar: cortarse es lo que evita el reintento horario.
        resultado = generate_invoice_pdf_and_email_task.call_local(uuid, 'http://t/')
        self.assertIsNone(resultado)

    def test_el_cliente_sin_correo_registra_el_motivo(self):
        from apps.core.tasks import generate_invoice_pdf_and_email_task

        self.customer.user.email = ''
        self.customer.user.save()

        with self._render_ok(), self.assertRaises(RuntimeError):
            generate_invoice_pdf_and_email_task.call_local(str(self.invoice.uuid), 'http://t/')

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.email_status, Invoice.EmailStatus.FAILED)
        self.assertIn('correo', self.invoice.email_error)


class SaludoDelCorreoTests(TestCase):
    """El saludo del correo imprimía `company_name`, que en una natural es NULL:
    Django no lo silencia, lo escribe literally como la palabra `None`, y el
    cliente leía "Estimado(a) None," en su propia factura."""

    @classmethod
    def setUpTestData(cls):
        cls.customer = natural_customer(
            User.objects.create_user(
                'saludo', 'saludo@ejemplo.cu', 'pass', first_name='Ana', last_name='Norte'
            )
        )
        cls.subscription = ServiceSubscription.objects.create(
            customer=cls.customer,
            service=Service.objects.create(
                user=cls.customer.user,
                title='Servicio de prueba',
                code='SRV-SALUDO',
                price=Decimal('100.00'),
            ),
        )
        cls.invoice = Invoice.objects.create(
            customer=cls.customer, number='INV-SALUDO', amount=Decimal('100.00')
        )
        InvoiceItem.objects.create(
            invoice=cls.invoice,
            descripcion='Item',
            cantidad=1,
            precio=Decimal('100.00'),
        )

    def test_factura_saluda_con_el_nombre_del_cliente_natural(self):
        for template in (
            'pages/commercial/emails/factura.html',
            'pages/commercial/emails/factura_qr.html',
        ):
            with self.subTest(template=template):
                html = render_to_string(
                    template,
                    {'invoice': self.invoice, 'customer': self.customer},
                )
                self.assertIn('Ana Norte', html)
                self.assertNotIn('>None<', html)

    def test_certificado_saluda_con_el_nombre_del_cliente_natural(self):
        html = render_to_string(
            'pages/commercial/emails/certificado.html',
            {'subscription': self.subscription, 'customer': self.customer},
        )
        self.assertIn('Ana Norte', html)
        self.assertNotIn('>None<', html)


class ResumenDelClienteTests(FacturaBase):
    """`_cliente_label` tiene que servir para los dos tipos de cliente.

    `company_name` solo lo llenan las jurídicas: si el resumen se queda solo
    con ese campo, toda factura de una persona natural —el caso más común del
    portal— aparece como 'Factura X · None'.
    """

    def _resumen(self):
        from apps.core.apps import _summary

        return _summary(None, f'invoice:{self.invoice.uuid}')

    def test_una_natural_se_identifica_con_sus_nombres(self):
        self.assertEqual(self._resumen(), 'Factura INV-ENTREGA · Ana Entrega')

    def test_una_natural_sin_nombre_cae_al_correo(self):
        self.user.first_name = ''
        self.user.last_name = ''
        self.user.save()

        self.assertEqual(self._resumen(), 'Factura INV-ENTREGA · entrega@ejemplo.cu')

    def test_una_natural_sin_nombres_ni_correo_cae_al_documento(self):
        self.user.first_name = ''
        self.user.last_name = ''
        self.user.email = ''
        self.customer.identity_document = '93091845266'
        self.user.save()
        self.customer.save()

        self.assertEqual(self._resumen(), 'Factura INV-ENTREGA · 93091845266')

    def test_una_juridica_se_identifica_con_la_razon_social(self):
        self.customer.client_type = 'juridica'
        self.customer.company_name = 'Empresa de Prueba SRL'
        self.customer.reeup = next_reeup()
        self.customer.nit = next_nit()
        self.customer.save()

        self.assertEqual(self._resumen(), 'Factura INV-ENTREGA · Empresa de Prueba SRL')

    def test_una_factura_sin_cliente_no_revienta_el_log(self):
        self.invoice.customer = None
        self.invoice.save()

        self.assertEqual(self._resumen(), 'Factura INV-ENTREGA · sin cliente')


class ClaveLogicaTests(FacturaBase):
    """El log identifica el trabajo lógico, no el intento.

    Estos tests encolan de verdad contra la cola, no usan `call_local`: las
    señales de Huey solo corren cuando la tarea pasa por la cola, y con
    `call_local` no se crearía ninguna fila de log (el camino síncrono del
    comando de pruebas tampoco la crea, y eso es lo correcto: no es una
    tarea de worker).
    """

    def test_reintentar_actualiza_la_misma_fila(self):
        from apps.core.tasks import generate_invoice_pdf_and_email_task

        generate_invoice_pdf_and_email_task(str(self.invoice.uuid), 'http://t/')
        log = TaskExecutionLog.objects.get(logical_key=f'invoice:{self.invoice.uuid}')
        primer_task_id = log.task_id
        intentos_iniciales = log.attempts
        TaskExecutionLog.objects.filter(pk=log.pk).update(
            status=TaskExecutionLog.STATUS_ERROR,
            error_message='SMTP caido',
        )

        generate_invoice_pdf_and_email_task(str(self.invoice.uuid), 'http://t/')

        clave = f'invoice:{self.invoice.uuid}'
        self.assertEqual(
            TaskExecutionLog.objects.filter(logical_key=clave).count(),
            1,
            'el reintento no debe abrir una fila nueva',
        )
        log.refresh_from_db()
        self.assertNotEqual(
            log.task_id,
            primer_task_id,
            'el id de intento tiene que refrescarse al de la tarea nueva',
        )
        self.assertEqual(log.status, TaskExecutionLog.STATUS_ENQUEUED)
        self.assertEqual(
            log.attempts,
            intentos_iniciales + 1,
            'los intentos se acumulan en la fila en vez de repartirse en varias',
        )

    def test_el_resumen_dice_de_quien_es_la_tarea(self):
        from apps.core.tasks import generate_invoice_pdf_and_email_task

        generate_invoice_pdf_and_email_task(str(self.invoice.uuid), 'http://t/')

        log = TaskExecutionLog.objects.get(logical_key=f'invoice:{self.invoice.uuid}')
        self.assertEqual(log.summary, 'Factura INV-ENTREGA · Ana Entrega')

    def test_una_factura_borrada_no_rompe_el_log(self):
        from apps.core.tasks import generate_invoice_pdf_and_email_task

        self.invoice.hard_delete()

        # Reencolar una factura inexistente no debe romper el signal.
        generate_invoice_pdf_and_email_task(str(self.invoice.uuid), 'http://t/')

        log = TaskExecutionLog.objects.filter(logical_key=f'invoice:{self.invoice.uuid}').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.summary, 'Factura (eliminado)')


@override_settings(EMAIL_BACKEND=LOCMEM)
class CorreoVisibleAlClienteTests(TestCase):
    """El correo de la factura, visto desde el cliente que lo recibe.

    Tres defectos con el mismo patrón: lo que el correo imprimía divergía de
    lo que el cliente podía ver o abrir.

    - El asunto se armaba con `company_name`, que en una persona natural es
      NULL: la f-string lo escribía literal como la palabra `None`.
    - El cuerpo citaba `cid:qr_pago.png`, pero el QR se adjuntaba con
      `attach(nombre, bytes, mimetype)`, que no pone cabecera `Content-ID`:
      el `cid:` no resolvía y el cliente veía el texto del `alt`.
    - «Ver en línea» apuntaba a facturación, que exige `view_invoice`, un
      permiso que el cliente no tiene; la página que sí puede abrir es
      «Mis Suscripciones» (`view_subscription`, el permiso del grupo
      `Clientes`).
    """

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        cls.user = User.objects.create_user(
            'clientecorreo',
            'cliente@ejemplo.cu',
            'pass',
            first_name='Ana',
            last_name='Norte',
        )
        cls.customer = natural_customer(cls.user)
        cls.subscription = ServiceSubscription.objects.create(
            customer=cls.customer,
            service=Service.objects.create(
                user=cls.user,
                title='Servicio con QR',
                code='SRV-CORREO-QR',
                price=Decimal('100.00'),
            ),
            payment_method='qr',
        )
        cls.invoice_qr = Invoice.objects.create(
            customer=cls.customer, number='INV-CORREO-QR', amount=Decimal('100.00')
        )
        InvoiceItem.objects.create(
            invoice=cls.invoice_qr,
            subscription=cls.subscription,
            descripcion='Item con QR',
            cantidad=1,
            precio=Decimal('100.00'),
        )
        cls.invoice_plana = Invoice.objects.create(
            customer=cls.customer, number='INV-CORREO-PLANA', amount=Decimal('100.00')
        )
        InvoiceItem.objects.create(
            invoice=cls.invoice_plana,
            descripcion='Item',
            cantidad=1,
            precio=Decimal('100.00'),
        )
        cls.base_url = 'http://testserver/'

    def setUp(self):
        # El outbox del backend locmem es a nivel de módulo: sin resetearlo,
        # un test leería los mensajes que dejó el anterior.
        mail.outbox = []

    def _enviar(self, invoice, customer=None):
        """Envía la factura de verdad (sin mocks) y devuelve el mensaje del outbox.

        Hace falta el mensaje MIME real: los defectos viven en las partes y
        cabeceras del correo, no en el objeto `EmailMessage`.
        """
        from apps.commercial.views.invoice_utils import enviar_correo_factura

        customer = customer or self.customer
        enviado = enviar_correo_factura(invoice, customer, base_url=self.base_url)
        self.assertTrue(enviado, 'el correo debe enviarse para poder inspeccionarlo')
        return mail.outbox[-1]

    def _dar_permiso_clientes(self):
        """`view_subscription` por el grupo `Clientes`, el camino no-staff."""
        grupo, _ = Group.objects.get_or_create(name='Clientes')
        permiso = ContentType.objects.get_for_model(ServiceSubscription).permission_set.get(
            codename='view_subscription'
        )
        grupo.permissions.add(permiso)
        self.user.groups.add(grupo)

    def test_el_asunto_de_una_persona_natural_lleva_su_nombre_y_no_none(self):
        mensaje = self._enviar(self.invoice_plana)

        self.assertIn('Ana Norte', mensaje.subject)
        self.assertNotIn('None', mensaje.subject)

    def test_el_asunto_de_una_juridica_usa_la_razon_social(self):
        """Mismo criterio que `display_name` en los cuerpos: la jurídica se
        identifica por su razón social. Triangula el criterio del asunto."""
        juridica = juridica_customer(username='corporreo')
        factura = Invoice.objects.create(
            customer=juridica, number='INV-CORREO-CORP', amount=Decimal('100.00')
        )
        InvoiceItem.objects.create(
            invoice=factura, descripcion='Item', cantidad=1, precio=Decimal('100.00')
        )

        mensaje = self._enviar(factura, customer=juridica)

        self.assertIn('Empresa de Prueba S.A.', mensaje.subject)
        self.assertNotIn('None', mensaje.subject)

    def test_el_qr_se_muestra_en_el_cuerpo_como_parte_inline(self):
        """El `cid:qr_pago.png` del cuerpo solo resuelve contra una parte con
        cabecera `Content-ID`; el adjunto por nombre no la trae."""
        mensaje = self._enviar(self.invoice_qr)

        self.assertIn('cid:qr_pago.png', mensaje.body)
        partes = [
            parte
            for parte in mensaje.message().walk()
            if parte.get('Content-ID') == '<qr_pago.png>'
        ]
        self.assertEqual(
            len(partes),
            1,
            'el cuerpo referencia cid:qr_pago.png: hace falta una parte con ese Content-ID',
        )
        payload = partes[0].get_payload(decode=True)
        self.assertTrue(
            payload.startswith(b'\x89PNG'),
            'la parte inline debe llevar los bytes del PNG, no un placeholder',
        )
        self.assertEqual(partes[0].get_content_disposition(), 'inline')

    def test_el_qr_no_viaja_duplicado_como_adjunto(self):
        """El PNG del QR debe viajar una sola vez: la parte inline con
        `Content-ID` es la única copia, para que el archivo no pese dos veces
        en el correo."""
        mensaje = self._enviar(self.invoice_qr)
        ruta = finders.find('dist/img/QR/QR.png')
        self.assertIsNotNone(ruta, 'el QR de pago debe existir en los estáticos del proyecto')
        with open(ruta, 'rb') as f:
            qr_bytes = f.read()

        nombres_adjuntos = [
            adjunto[0] for adjunto in mensaje.attachments if isinstance(adjunto, tuple)
        ]
        self.assertNotIn(
            'qr_pago.png',
            nombres_adjuntos,
            'el QR no debe adjuntarse por nombre: sería una segunda copia del PNG',
        )
        adjuntos_con_qr = [
            parte
            for parte in mensaje.message().walk()
            if parte.get_content_disposition() == 'attachment'
            and parte.get_payload(decode=True) == qr_bytes
        ]
        self.assertEqual(
            adjuntos_con_qr,
            [],
            'ninguna parte con Content-Disposition: attachment debe llevar los bytes del QR',
        )

        partes = [
            parte
            for parte in mensaje.message().walk()
            if parte.get('Content-ID') == '<qr_pago.png>'
        ]
        self.assertEqual(
            len(partes),
            1,
            'hace falta exactamente una parte con Content-ID <qr_pago.png>',
        )
        self.assertEqual(partes[0].get_content_type(), 'image/png')
        self.assertEqual(
            partes[0].get_payload(decode=True),
            qr_bytes,
            'la parte inline única debe llevar los bytes del QR, no un placeholder',
        )

    def test_ver_en_linea_apunta_a_suscripciones_y_no_a_facturacion(self):
        """Las dos plantillas leen la misma clave `listado_url`: si apunta a
        facturación, el cliente cae en una página que no puede abrir."""
        suscripciones = reverse('commercial:suscripcion_list')
        facturacion = reverse('commercial:factura_list')

        for invoice in (self.invoice_plana, self.invoice_qr):
            with self.subTest(invoice=invoice.number):
                mensaje = self._enviar(invoice)
                self.assertIn(self.base_url + suscripciones.lstrip('/'), mensaje.body)
                self.assertNotIn(facturacion, mensaje.body)

    def test_el_cliente_puede_abrir_el_listado_que_el_correo_enlaza(self):
        """`view_subscription` sí lo tiene el grupo `Clientes`; `view_invoice`,
        no. El enlace del correo tiene que caer del lado alcanzable."""
        self.client.force_login(self.user)
        facturacion = reverse('commercial:factura_list')
        self.assertIn(
            self.client.get(facturacion).status_code,
            (302, 403),
            'sin view_invoice el cliente no puede abrir facturación',
        )

        self._dar_permiso_clientes()
        suscripciones = reverse('commercial:suscripcion_list')
        respuesta = self.client.get(suscripciones)
        self.assertEqual(
            respuesta.status_code,
            200,
            'el enlace del correo debe llevar a una página que el cliente sí puede abrir',
        )
