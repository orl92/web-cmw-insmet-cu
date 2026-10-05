"""Entrega de la factura: PDF y correo como pasos con estado propio.

Estos tests fijan el comportamiento que reportaba el operador:

- el PDF se renderiza una vez y no se vuelve a renderizar cuando lo que
  falla es el correo;
- los botones de ver/descargar existen solo cuando el PDF quedó `ready`;
- reintentar una tarea actualiza su fila en el log, no abre una nueva;
- la tabla de tareas dice de qué cliente es cada una;
- una factura borrada con la tarea en la cola no genera reintentos para siempre.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.test import TestCase

from apps.commercial.models import Invoice, InvoiceItem, Service, ServiceSubscription
from apps.commercial.tests.factories import natural_customer
from apps.core.models import TaskExecutionLog
from config.huey import huey


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
