"""Ejercita de punta a punta el flujo de factura: PDF + correo, por el worker de Huey.

El problema que este comando viene a resolver: en desarrollo el flujo se ve
"simulado" por cuatro razones apiladas (falta el binario de PDF, la tarea muere
antes de enviar, el worker no arranca sin `logs/`, y el console backend nunca
falla). Con este comando el preflight dice cuál de esas está fallando, en vez de
dejar que se manifieste como un reintento de Huey o como un `email_sent=True` que
no llegó a ningún lado.
"""

from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.commercial.models import Customer, Invoice, InvoiceItem
from apps.commercial.views.invoice_utils import require_pdf_renderer

# Backends que no entregan a nadie: escriben y devuelven éxito igual. Con estos,
# `email_sent=True` no significa que el correo saliera.
SILENT_BACKENDS = {
    'django.core.mail.backends.console.EmailBackend',
    'django.core.mail.backends.filebased.EmailBackend',
    'django.core.mail.backends.locmem.EmailBackend',
}

DEMO_USERNAME = 'demo_factura'


class Command(BaseCommand):
    help = (
        'Encola (o ejecuta) la tarea del worker que genera el PDF de una factura y '
        'envía el correo. Con --demo crea los datos mínimos para no depender de una '
        'factura existente.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'invoice_uuid',
            nargs='?',
            help='UUID de la factura a procesar. Omitilo si usás --demo.',
        )
        parser.add_argument(
            '--demo',
            action='store_true',
            help='Crea cliente, factura e item mínimos y los usa.',
        )
        parser.add_argument(
            '--email',
            default='cliente.demo@example.com',
            help='Correo del cliente de prueba cuando usás --demo.',
        )
        parser.add_argument(
            '--now',
            action='store_true',
            help=(
                'Ejecuta la tarea en este proceso en vez de encolarla. No prueba el '
                'worker: sirve para ver el resultado sin levantar el consumer.'
            ),
        )
        parser.add_argument(
            '--base-url',
            default=None,
            help='URL base del sitio para los links del correo. Por defecto settings.BASE_URL.',
        )

    def handle(self, *args, **options):
        if not options['invoice_uuid'] and not options['demo']:
            raise CommandError('Pasá el UUID de una factura o usá --demo.')

        # El renderizador se chequea antes de tocar la base: es una dependencia del
        # sistema, no de la factura. Al revés, un `--demo` en una máquina sin
        # wkhtmltopdf deja datos creados que no va a poder usar.
        self._preflight_renderer()

        invoice = (
            self._build_demo_invoice(options['email'])
            if options['demo']
            else self._get_invoice(options['invoice_uuid'])
        )

        base_url = options['base_url'] or getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000/')

        self._preflight_customer(invoice)
        self._report_backend()

        if options['now']:
            self._run_now(invoice, base_url)
        else:
            self._enqueue(invoice, base_url)

    # --- datos -------------------------------------------------------------

    def _get_invoice(self, invoice_uuid):
        try:
            invoice = Invoice.objects.get(uuid=invoice_uuid)
        except (Invoice.DoesNotExist, ValueError, TypeError) as exc:
            raise CommandError(f'No existe una factura con uuid={invoice_uuid!r}.') from exc
        self.stdout.write(f'Factura {invoice.number} ({invoice.uuid})')
        return invoice

    def _build_demo_invoice(self, email):
        user_model = get_user_model()
        user, _ = user_model.objects.get_or_create(
            username=DEMO_USERNAME,
            defaults={'email': email, 'first_name': 'Cliente', 'last_name': 'Demo'},
        )
        # El correo se actualiza siempre: si el usuario ya existe de una corrida
        # anterior, se manda al destino de esta corrida y no al de la anterior.
        if user.email != email:
            user.email = email
            user.save(update_fields=['email'])

        customer, _ = Customer.objects.get_or_create(
            user=user,
            defaults={
                'client_type': Customer.ClientType.JURIDICA,
                'company_name': 'Empresa de prueba',
                'phone': '+53 00000000',
            },
        )

        invoice = Invoice.objects.create(
            customer=customer,
            number=f'DEMO-{Invoice.objects.count() + 1:04d}',
            amount=Decimal('100.00'),
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            descripcion='Servicio meteorological de prueba',
            cantidad=Decimal('1'),
            unidad_medida='U',
            precio=Decimal('100.00'),
        )
        self.stdout.write(
            self.style.WARNING(
                f'Datos de prueba creados: factura {invoice.number} ({invoice.uuid})'
            )
        )
        return invoice

    def _resolve_customer(self, invoice):
        """Misma resolución de cliente que la vista de reenvío, para que el preflight
        no approve algo que la vista rechazaría."""
        if invoice.subscription:
            return invoice.subscription.customer
        if invoice.customer:
            return invoice.customer
        first_item = invoice.items.first()
        if first_item and first_item.subscription:
            return first_item.subscription.customer
        return None

    # --- preflight ---------------------------------------------------------

    def _preflight_renderer(self):
        try:
            require_pdf_renderer()
        except RuntimeError as exc:
            self.stdout.write(self.style.ERROR('  [falta] wkhtmltopdf'))
            raise CommandError(
                f'Preflight fallido:\n\n{exc}\n\nNo se creó ni encoló nada.'
            ) from exc
        self.stdout.write(self.style.SUCCESS('  [ok] wkhtmltopdf instalado'))

    def _preflight_customer(self, invoice):
        customer = self._resolve_customer(invoice)
        if not customer:
            raise CommandError(
                'Preflight fallido:\n\n'
                'La factura no tiene cliente resoluble (ni por suscripción, ni por '
                'customer, ni por el item más antiguo).\n\n'
                'No se encoló nada.'
            )
        if not customer.user or not customer.user.email:
            raise CommandError(
                f'Preflight fallido:\n\nEl cliente {customer} no tiene usuario con '
                'correo, que es lo que exige el envío.\n\nNo se encoló nada.'
            )
        self.stdout.write(self.style.SUCCESS(f'  [ok] cliente con correo: {customer.user.email}'))

    def _report_backend(self):
        backend = settings.EMAIL_BACKEND
        if backend in SILENT_BACKENDS:
            self.stdout.write(
                self.style.WARNING(
                    f'  [aviso] EMAIL_BACKEND={backend}\n'
                    f'          Este backend no entrega a nadie: escribe el mensaje y '
                    f'devuelve éxito igual.\n'
                    f'          Para ver el correo real, poné en el .env:\n'
                    f'            EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend\n'
                    f'          y queda como archivo .log en {settings.EMAIL_FILE_PATH}'
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS(f'  [ok] EMAIL_BACKEND={backend}'))

    # --- ejecución ---------------------------------------------------------

    def _enqueue(self, invoice, base_url):
        from apps.core.tasks import generate_invoice_pdf_and_email_task

        generate_invoice_pdf_and_email_task(str(invoice.uuid), base_url)
        self.stdout.write(
            self.style.WARNING(
                f'Encolado en {settings.BASE_DIR}/huey.db. ENCOLADO, NO ENVIADO.\n'
                f'Para que salga: ./run_huey.sh  (log en logs/huey.log)'
            )
        )

    def _run_now(self, invoice, base_url):
        from apps.core.tasks import generate_invoice_pdf_and_email_task

        try:
            generate_invoice_pdf_and_email_task.call_local(str(invoice.uuid), base_url)
        except Exception as exc:
            invoice.refresh_from_db()
            self.stderr.write(
                self.style.ERROR(
                    f'La tarea falló: {type(exc).__name__}: {exc}\n'
                    f'Revisá logs/huey.log si esperabas que el worker lo reintentara.'
                )
            )
            raise CommandError('La tarea del worker falló.') from exc

        invoice.refresh_from_db()
        if invoice.email_sent:
            recipient = self._resolve_customer(invoice).user.email
            self.stdout.write(
                self.style.SUCCESS(
                    f'Factura {invoice.number}: email_sent=True, correo a {recipient}'
                )
            )
        else:
            self.stderr.write(
                self.style.ERROR(
                    f'Factura {invoice.number}: email_sent=False, '
                    f'email_error={invoice.email_error!r}'
                )
            )
            raise CommandError('La tarea corrió pero el correo no se envió.')
