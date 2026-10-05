import os
import shutil
import tempfile
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from huey.storage import SqliteStorage

from apps.commercial.management.commands.send_test_invoice import (
    DEMO_NATURAL_IDENTITY_DOCUMENT,
    DEMO_PREFIX,
    DEMO_USERNAME_PREFIX,
)
from apps.commercial.models import (
    Contract,
    Customer,
    Invoice,
    InvoiceItem,
    Service,
    ServiceSubscription,
)
from apps.commercial.views.invoice_utils import require_pdf_renderer

# El comando importa `require_pdf_renderer` por nombre, así que para simular una
# máquina sin la pila de Pango hay que parchear el símbolo donde se usa (el comando),
# no donde está definido (`invoice_utils`).
PREFLIGHT = 'apps.commercial.management.commands.send_test_invoice.require_pdf_renderer'
# Para probar el preflight real hay que tocar el motor que él invoca.
MOTOR = 'apps.commercial.views.invoice_utils.HTML'

ERROR_MOTOR = (
    'No se puede generar el PDF de la factura: faltan bibliotecas del sistema '
    'necesarias para WeasyPrint (Pango/Harfbuzz).'
)


def con_binario():
    """El preflight se pasa por alto: simula que la pila de Pango funciona."""
    return patch(PREFLIGHT, return_value=None)


def sin_weasyprint():
    """La máquina de desarrollo sin la pila de sistema que necesita WeasyPrint."""

    def _falla():
        raise RuntimeError(ERROR_MOTOR)

    return patch(PREFLIGHT, _falla)


class RequirePdfRendererTests(TestCase):
    """Acá se prueba el preflight de verdad: se le rompe el motor por debajo.

    `require_pdf_renderer` está cacheado por proceso para no pagar el arranque de
    Pango en cada factura, así que hay que limpiar la cache alrededor del test o
    el resultado del caso anterior se filtra.
    """

    def setUp(self):
        require_pdf_renderer.cache_clear()
        self.addCleanup(require_pdf_renderer.cache_clear)

    def test_pasa_cuando_el_motor_genera_pdf(self):
        with patch(MOTOR, autospec=True):
            self.assertIsNone(require_pdf_renderer())

    def test_falla_con_instruccion_cuando_al_motor_le_falta_la_pila(self):
        with patch(MOTOR, autospec=True) as motor:
            motor.return_value.write_pdf.side_effect = OSError('cannot load library')
            with self.assertRaises(RuntimeError) as ctx:
                require_pdf_renderer()

        mensaje = str(ctx.exception)
        # El error tiene que decir qué instalar: el error crudo de Pango no lo
        # hace, y en el worker se ve como un reintento.
        self.assertIn('apt install', mensaje)
        self.assertIn('libharfbuzz0b', mensaje)


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
        Invoice.objects.filter(number='CMD-0001').update(
            email_status='sent' if enviada else 'failed',
            email_error=error or None,
            pdf_status='ready',
        )

    def _marcar_demo_enviada(self, enviada=True, error=''):
        """Ídem, sobre las facturas que crea `--demo` (su número no es fijo)."""
        Invoice.objects.filter(number__startswith=DEMO_PREFIX).update(
            email_status='sent' if enviada else 'failed',
            email_error=error or None,
            pdf_status='ready',
        )

    def _cola_sqlite(self):
        """Pone en la cola de Huey el backend real de desarrollo.

        `IsolatedMediaRunner` deja un `MemoryStorage` mientras corren los tests,
        y ese backend no tiene el SQL que usa `--purge-demo` para borrar una
        tarea puntual. Con un `SqliteStorage` en un temporal se prueba el camino
        de producción sin tocar el `huey.db` de la base de desarrollo.
        """
        from config.huey import huey

        original = huey.storage
        tmp = tempfile.mkdtemp(prefix='huey_test_')
        huey.storage = SqliteStorage(huey.name, filename=os.path.join(tmp, 'huey.db'))
        self.addCleanup(lambda: (setattr(huey, 'storage', original), shutil.rmtree(tmp, True)))

    def _encoladas(self):
        from config.huey import huey

        return [str(m.args[0]) for m in list(huey.pending()) + list(huey.scheduled())]

    # --- argumentos --------------------------------------------------------

    def test_sin_uuid_ni_demo_es_error(self):
        with self.assertRaises(CommandError):
            self._run()

    def test_uuid_inexistente_es_error(self):
        # El preflight del renderizador va primero, así que hay que simular que el
        # motor funciona para que el comando llegue a buscar la factura.
        with con_binario(), self.assertRaises(CommandError) as ctx:
            self._run('00000000-0000-0000-0000-000000000000')

        self.assertIn('No existe una factura', str(ctx.exception))

    # --- preflight ---------------------------------------------------------

    def test_demo_con_falta_de_motor_no_crea_datos(self):
        """El chequeo del renderizador va antes de la base: si fallara después,
        un --demo dejaría facturas que no se pueden usar."""
        with sin_weasyprint(), self.assertRaises(CommandError) as ctx:
            self._run('--demo', '--escribir-en-dev', '--encolar')

        self.assertIn('WeasyPrint', str(ctx.exception))
        self.assertFalse(Invoice.objects.filter(number__startswith=DEMO_PREFIX).exists())

    # --- opt-in de escritura ------------------------------------------------

    def test_demo_sin_el_optin_no_escribe_nada(self):
        """`--demo` escribe filas reales en la base de desarrollo: sin
        `--escribir-en-dev` no se toca nada, ni siquiera después del preflight."""
        with con_binario(), self.assertRaises(CommandError) as ctx:
            self._run('--demo')

        mensaje = str(ctx.exception)
        # El error tiene que decir exactamente qué correr, no solo que "falta algo".
        self.assertIn('--demo --escribir-en-dev', mensaje)
        self.assertIn('--purge-demo', mensaje)
        self.assertFalse(User.objects.filter(username__startswith=DEMO_USERNAME_PREFIX).exists())
        self.assertFalse(Invoice.objects.filter(number__startswith=DEMO_PREFIX).exists())

    def test_el_optin_solo_alcanza_al_demo(self):
        """Una factura existente no necesita opt-in: el flag protege lo que el
        demo escribe, no el flujo normal."""
        with con_binario(), patch('apps.core.tasks.generate_invoice_pdf_and_email_task'):
            salida = self._run(str(self.invoice.uuid), '--encolar')

        self.assertIn('ENCOLADO', salida)
        self.assertNotIn('--purge-demo', salida)

    def test_demo_con_optin_crea_los_dos_tipos_de_cliente(self):
        """El PDF tiene dos bloques de cliente: un demo de un solo tipo dejaría
        sin probar la mitad del template."""
        with con_binario(), patch('apps.core.tasks.generate_invoice_pdf_and_email_task'):
            salida = self._run('--demo', '--escribir-en-dev', '--encolar')

        tipos = set(
            Customer.objects.filter(user__username__startswith=DEMO_USERNAME_PREFIX).values_list(
                'client_type', flat=True
            )
        )
        self.assertEqual(tipos, {'juridica', 'natural'})
        natural = Customer.objects.get(client_type='natural')
        self.assertEqual(natural.identity_document, DEMO_NATURAL_IDENTITY_DOCUMENT)
        self.assertTrue(Contract.objects.exists())
        self.assertEqual(Invoice.objects.filter(number__startswith=DEMO_PREFIX).count(), 2)
        # Y dice cómo deshacerse de todo eso.
        self.assertIn('--purge-demo', salida)

    # --- limpieza -----------------------------------------------------------

    def test_purge_demo_borra_todo_lo_que_creo_el_demo(self):
        with con_binario(), patch('apps.core.tasks.generate_invoice_pdf_and_email_task'):
            self._run('--demo', '--escribir-en-dev', '--encolar')

        invoices = list(Invoice.objects.filter(number__startswith=DEMO_PREFIX))
        for invoice in invoices:
            invoice.pdf.save('factura_demo.pdf', ContentFile(b'%PDF-1.4 demo'))
            invoice.refresh_from_db()
        rutas = [Path(settings.MEDIA_ROOT) / invoice.pdf.name for invoice in invoices]
        self.assertTrue(all(ruta.exists() for ruta in rutas))

        salida = self._run('--purge-demo')

        self.assertFalse(User.objects.filter(username__startswith=DEMO_USERNAME_PREFIX).exists())
        self.assertFalse(
            Customer.objects.filter(user__username__startswith=DEMO_USERNAME_PREFIX).exists()
        )
        self.assertFalse(Invoice.objects.filter(number__startswith=DEMO_PREFIX).exists())
        self.assertFalse(
            InvoiceItem.objects.filter(invoice__number__startswith=DEMO_PREFIX).exists()
        )
        self.assertFalse(Contract.objects.exists())
        self.assertFalse(ServiceSubscription.objects.exists())
        self.assertFalse(Service.objects.filter(code__startswith=DEMO_PREFIX).exists())
        # `hard_delete()` y no `delete()`: si fuera lógico, las filas seguirían ahí
        # con record_active=False y la base seguiría sucia.
        self.assertIn('borrados', salida)
        for ruta in rutas:
            self.assertFalse(ruta.exists())

    def test_purge_demo_no_toca_al_admin_ni_a_datos_reales(self):
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'pass')
        real_user = User.objects.create_user('cliente_real', 'real@example.com', 'pass')
        real_customer = Customer.objects.create(
            client_type='juridica',
            user=real_user,
            company_name='Empresa Real',
            account='9001000000000900',
            address='Dir',
            phone='71234567',
        )
        real_invoice = Invoice.objects.create(
            customer=real_customer,
            number='REAL-0001',
            amount=Decimal('10.00'),
        )

        with con_binario(), patch('apps.core.tasks.generate_invoice_pdf_and_email_task'):
            self._run('--demo', '--escribir-en-dev', '--encolar')
        # Un superuser con el prefijo del demo tiene que sobrevivir igual:
        # el filtro de staff va en la consulta, no después.
        User.objects.filter(pk=admin.pk).update(username=f'{DEMO_USERNAME_PREFIX}_admin')

        self._run('--purge-demo')

        self.assertTrue(User.objects.filter(pk=admin.pk).exists())
        self.assertTrue(Customer.objects.filter(pk=real_customer.pk).exists())
        self.assertTrue(Invoice.objects.filter(pk=real_invoice.pk).exists())

    def test_purge_demo_saca_sus_tareas_de_la_cola_de_huey(self):
        """Con `--encolar` el demo deja trabajo en la cola compartida con
        `run_huey.sh`. La tarea hace `Invoice.objects.get(uuid=...)` sin tolerar
        `DoesNotExist`, así que si el purge borrara las facturas y dejara las
        tareas, el worker se comería un `DoesNotExist` por cada una, con tres
        reintentos y backoff."""
        # El runner de tests mete un `MemoryStorage` en la cola, que no soporta
        # el borrado puntual por SQL que hace el purge. Acá va el backend real
        # (SQLite en un archivo temporal), que es el de desarrollo.
        self.enterContext(con_binario())
        self._cola_sqlite()

        self._run('--demo', '--escribir-en-dev', '--encolar')
        invoices = list(Invoice.objects.filter(number__startswith=DEMO_PREFIX))
        otra = Invoice.objects.create(
            customer=invoices[0].customer,
            number='REAL-ENCOLADA-0001',
            amount=Decimal('10.00'),
        )
        # Una tarea ajena al demo, que el purge no puede tocar.
        from apps.core.tasks import generate_invoice_pdf_and_email_task

        generate_invoice_pdf_and_email_task(str(otra.uuid), 'http://testserver/')
        self.assertEqual(len(self._encoladas()), 3)

        self._run('--purge-demo')

        self.assertFalse(Invoice.objects.filter(number__startswith=DEMO_PREFIX).exists())
        self.assertTrue(Invoice.objects.filter(pk=otra.pk).exists())
        self.assertEqual(
            self._encoladas(), [str(otra.uuid)], 'solo debe quedar la tarea ajena al demo'
        )

    def test_demo_por_default_no_deja_nada_en_la_cola(self):
        """El camino por defecto ejecuta la tarea en el proceso. Encolar deja
        trabajo vivo en una cola compartida, así que tiene que ser opt-in."""
        from config.huey import huey

        with con_binario(), patch('apps.core.tasks.generate_invoice_pdf_and_email_task') as tarea:
            tarea.call_local.side_effect = lambda *a, **kw: self._marcar_demo_enviada()
            self._run('--demo', '--escribir-en-dev')

        self.assertTrue(Invoice.objects.filter(number__startswith=DEMO_PREFIX).exists())
        self.assertEqual(huey.scheduled_count(), 0)
        self.assertEqual(huey.pending_count(), 0)

    def test_purge_demo_sin_datos_no_falla(self):
        salida = self._run('--purge-demo')

        self.assertIn('No hay datos del demo', salida)

    def test_purge_demo_no_necesita_el_optin_ni_el_motor(self):
        """La limpieza no puede quedar bloqueada por el preflight: si el motor de
        PDF está roto, el `--purge-demo` es justo lo que hace falta."""
        with sin_weasyprint():
            salida = self._run('--purge-demo')

        self.assertIn('No hay datos del demo', salida)
        self.assertNotIn('WeasyPrint', salida)

    def test_cliente_sin_correo_es_error(self):
        self.user.email = ''
        self.user.save(update_fields=['email'])

        with con_binario(), self.assertRaises(CommandError) as ctx:
            self._run(str(self.invoice.uuid))

        self.assertIn('no tiene usuario con correo', str(ctx.exception))

    def test_avisa_que_el_backend_silencioso_no_entrega(self):
        with con_binario(), patch('apps.core.tasks.generate_invoice_pdf_and_email_task'):
            salida = self._run(str(self.invoice.uuid), '--encolar')

        self.assertIn('no entrega a nadie', salida)
        self.assertIn('filebased', salida)

    # --- ejecución ---------------------------------------------------------

    def test_encolar_deja_la_tarea_en_la_cola_y_no_dice_que_envio(self):
        with con_binario(), patch('apps.core.tasks.generate_invoice_pdf_and_email_task') as tarea:
            salida = self._run(str(self.invoice.uuid), '--encolar')

        tarea.assert_called_once()
        self.assertEqual(tarea.call_args[0][0], str(self.invoice.uuid))
        # Encolar no es enviar: el comando tiene que distinguirlo, porque es
        # exactamente la confusión que hace pensar que el flujo está simulado.
        self.assertIn('NO ENVIADO', salida)
        self.assertIn('run_huey.sh', salida)

    def test_por_default_ejecuta_la_tarea_en_el_proceso(self):
        """Sin `--encolar` no queda nada en la cola: la tarea corre acá."""
        from config.huey import huey

        with con_binario(), patch('apps.core.tasks.generate_invoice_pdf_and_email_task') as tarea:
            tarea.call_local.side_effect = lambda *a, **kw: self._marcar_enviada(True)
            salida = self._run(str(self.invoice.uuid))

        tarea.call_local.assert_called_once()
        self.assertEqual(huey.scheduled_count(), 0)
        self.assertEqual(huey.pending_count(), 0)
        self.assertNotIn('NO ENVIADO', salida)

    def test_now_usa_call_local_y_reporta_el_resultado_real(self):
        with con_binario(), patch('apps.core.tasks.generate_invoice_pdf_and_email_task') as tarea:
            tarea.call_local.side_effect = lambda *a, **kw: self._marcar_enviada(True)
            salida = self._run(str(self.invoice.uuid), '--now')

        tarea.call_local.assert_called_once()
        self.assertNotIn('NO ENVIADO', salida)
        self.assertIn('correo enviado', salida)

    def test_now_falla_cuando_el_correo_no_salio(self):
        def _falla_el_correo(*a, **kw):
            # La tarea real propaga el fallo del correo en vez de tragárselo:
            # el estado y el error quedan escritos y después sube la excepción.
            self._marcar_enviada(False, 'SMTP caído')
            raise RuntimeError('No se pudo enviar el correo de la factura CMD-0001')

        with con_binario(), patch('apps.core.tasks.generate_invoice_pdf_and_email_task') as tarea:
            tarea.call_local.side_effect = _falla_el_correo
            with self.assertRaises(CommandError) as ctx:
                self._run(str(self.invoice.uuid), '--now')

        self.assertIn('paso "correo"', str(ctx.exception))
