from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.commercial.models import Customer, Invoice
from apps.commercial.views.invoice_utils import require_pdf_renderer

# El preflight busca el binario con `shutil.which` dentro de `invoice_utils`, no en
# el comando: el parche va donde se usa, no donde se llama.
WHICH = 'apps.commercial.views.invoice_utils.shutil.which'
BINARIO = '/usr/bin/wkhtmltopdf'


def con_binario():
    """El preflight se pasa por alto: simula que wkhtmltopdf está instalado."""
    return patch(WHICH, return_value=BINARIO)


def sin_wkhtmltopdf():
    """La máquina de desarrollo sin el binario del sistema."""
    return patch(WHICH, return_value=None)


class RequirePdfRendererTests(TestCase):
    def test_pasa_cuando_el_binario_esta_en_el_path(self):
        with con_binario():
            self.assertIsNone(require_pdf_renderer())

    def test_falla_con_instruccion_cuando_falta_el_binario(self):
        with sin_wkhtmltopdf(), self.assertRaises(RuntimeError) as ctx:
            require_pdf_renderer()

        mensaje = str(ctx.exception)
        # El error tiene que decir qué instalar: el de pdfkit ("No wkhtmltopdf
        # executable found") no lo hace, y en el worker se ve como un reintento.
        self.assertIn('apt install wkhtmltopdf', mensaje)
        self.assertIn('wrapper', mensaje)


class SendTestInvoiceCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('cliente', 'cliente@example.com', 'pass')
        cls.customer = Customer.objects.create(
            client_type='juridica',
            user=cls.user,
            company_name='Empresa Test',
        )
        cls.invoice = Invoice.objects.create(
            customer=cls.customer,
            number='CMD-0001',
            amount=Decimal('50.00'),
        )

    def _run(self, *args, **kwargs):
        out, err = StringIO(), StringIO()
        call_command('send_test_invoice', *args, stdout=out, stderr=err, **kwargs)
        return out.getvalue() + err.getvalue()

    def _marcar_enviada(self, enviada, error=''):
        """Lo que hace `enviar_correo_factura` sobre la factura, sin el correo."""
        Invoice.objects.filter(number='CMD-0001').update(email_sent=enviada, email_error=error)

    # --- argumentos --------------------------------------------------------

    def test_sin_uuid_ni_demo_es_error(self):
        with self.assertRaises(CommandError):
            self._run()

    def test_uuid_inexistente_es_error(self):
        # El preflight del renderizador va primero, así que hay que simular que el
        # binario está para que el comando llegue a buscar la factura.
        with con_binario(), self.assertRaises(CommandError) as ctx:
            self._run('00000000-0000-0000-0000-000000000000')

        self.assertIn('No existe una factura', str(ctx.exception))

    # --- preflight ---------------------------------------------------------

    def test_demo_con_falta_de_binario_no_crea_datos(self):
        """El chequeo del renderizador va antes de la base: si fallara después,
        un --demo dejaría facturas que no se pueden usar."""
        with sin_wkhtmltopdf(), self.assertRaises(CommandError) as ctx:
            self._run('--demo')

        self.assertIn('wkhtmltopdf', str(ctx.exception))
        self.assertFalse(Invoice.objects.filter(number__startswith='DEMO').exists())

    def test_cliente_sin_correo_es_error(self):
        self.user.email = ''
        self.user.save(update_fields=['email'])

        with con_binario(), self.assertRaises(CommandError) as ctx:
            self._run(str(self.invoice.uuid))

        self.assertIn('no tiene usuario con correo', str(ctx.exception))

    def test_avisa_que_el_backend_silencioso_no_entrega(self):
        with con_binario(), patch('apps.core.tasks.generate_invoice_pdf_and_email_task'):
            salida = self._run(str(self.invoice.uuid))

        self.assertIn('no entrega a nadie', salida)
        self.assertIn('filebased', salida)

    # --- ejecución ---------------------------------------------------------

    def test_encola_la_tarea_y_no_dice_que_envio(self):
        with con_binario(), patch('apps.core.tasks.generate_invoice_pdf_and_email_task') as tarea:
            salida = self._run(str(self.invoice.uuid))

        tarea.assert_called_once()
        self.assertEqual(tarea.call_args[0][0], str(self.invoice.uuid))
        # Encolar no es enviar: el comando tiene que distinguirlo, porque es
        # exactamente la confusión que hace pensar que el flujo está simulado.
        self.assertIn('NO ENVIADO', salida)
        self.assertIn('run_huey.sh', salida)

    def test_now_usa_call_local_y_reporta_el_resultado_real(self):
        with con_binario(), patch('apps.core.tasks.generate_invoice_pdf_and_email_task') as tarea:
            tarea.call_local.side_effect = lambda *a, **kw: self._marcar_enviada(True)
            salida = self._run(str(self.invoice.uuid), '--now')

        tarea.call_local.assert_called_once()
        self.assertNotIn('NO ENVIADO', salida)
        self.assertIn('email_sent=True', salida)

    def test_now_falla_cuando_el_correo_no_salio(self):
        with con_binario(), patch('apps.core.tasks.generate_invoice_pdf_and_email_task') as tarea:
            tarea.call_local.side_effect = lambda *a, **kw: self._marcar_enviada(
                False, 'SMTP caído'
            )
            with self.assertRaises(CommandError) as ctx:
                self._run(str(self.invoice.uuid), '--now')

        self.assertIn('el correo no se envió', str(ctx.exception))
