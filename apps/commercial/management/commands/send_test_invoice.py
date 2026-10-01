"""Ejercita de punta a punta el flujo de factura: PDF + correo, por el worker de Huey.

El problema que este comando viene a resolver: en desarrollo el flujo se ve
"simulado" por cuatro razones apiladas (falta el binario de PDF, la tarea muere
antes de enviar, el worker no arranca sin `logs/`, y el console backend nunca
falla). Con este comando el preflight dice cuál de esas está fallando, en vez de
dejar que se manifieste como un reintento de Huey o como un
`email_status='sent'` que no llegó a ningún lado.

`--demo` escribe filas REALES (clientes, facturas, usuarios) en la base de
desarrollo. Como la base de desarrollo es la que el resto del trabajo usa, se
exige `--escribir-en-dev` para habilitarlo y se ofrece `--purge-demo` para
borrar todo lo que dejó. El PDF tiene dos bloques distintos según el tipo de
cliente, así que el demo crea uno de cada tipo con su contrato.
"""

import contextlib
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.commercial.models import (
    Contract,
    Customer,
    Invoice,
    InvoiceItem,
    Service,
    ServiceSubscription,
)
from apps.commercial.views.invoice_utils import require_pdf_renderer

# Backends que no entregan a nadie: escriben y devuelven éxito igual. Con estos,
# `email_status='sent'` no significa que el correo saliera.
SILENT_BACKENDS = {
    'django.core.mail.backends.console.EmailBackend',
    'django.core.mail.backends.filebased.EmailBackend',
    'django.core.mail.backends.locmem.EmailBackend',
}

# Todo lo que crea `--demo` queda marcado con uno de estos prefijos: es lo que
# `--purge-demo` usa para borrar, y lo que evita depender del título de la
# factura o del nombre de la empresa para reconocer una fila propia.
DEMO_USERNAME_PREFIX = 'demo_factura'
DEMO_PREFIX = 'DEMO-'

# Cola de Huey: el nombre con el que se registra `generate_invoice_pdf_and_email_task`.
# Huey lo registra con el nombre pelado o con el módulo según la versión, así que
# la comparación va por el sufijo. Lo que identifica una tarea del demo de verdad
# es el UUID de la factura en `args[0]`, no el nombre.
DEMO_TASK_NAME_SUFFIX = 'generate_invoice_pdf_and_email_task'

# Datos fijos del demo, pensados para ser válidos frente a los validadores del
# modelo (REEUP, NIT, cuenta y teléfono) y para que el PDF se vea real.
DEMO_NATURAL_IDENTITY_DOCUMENT = '34111234567'


class Command(BaseCommand):
    help = (
        'Encola (o ejecuta) la tarea del worker que genera el PDF de una factura y '
        'envía el correo. Con --demo crea los datos mínimos para no depender de una '
        'factura existente. Con --purge-demo borra los que dejó.'
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
            help=(
                'Crea cliente, factura e item mínimos y los usa. Escribe en la base '
                'de verdad: requiere --escribir-en-dev.'
            ),
        )
        parser.add_argument(
            '--escribir-en-dev',
            action='store_true',
            help=(
                'Opt-in explícito para lo que --demo escribe. Sin este flag --demo '
                'se niega a correr.'
            ),
        )
        parser.add_argument(
            '--purge-demo',
            action='store_true',
            help=(
                'Borra los datos que dejaron las corridas con --demo. No requiere ningún otro flag.'
            ),
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
                'Ejecuta la tarea en este proceso en vez de encolarla. Es el '
                'comportamiento por defecto. No prueba el worker: sirve para ver '
                'el resultado sin levantar el consumer.'
            ),
        )
        parser.add_argument(
            '--encolar',
            action='store_true',
            help=(
                'Deja la tarea en la cola de Huey para que la tome run_huey.sh, en '
                'vez de ejecutarla acá. Solo para probar el camino del worker: deja '
                'trabajo pendiente en la cola compartida.'
            ),
        )
        parser.add_argument(
            '--base-url',
            default=None,
            help='URL base del sitio para los links del correo. Por defecto settings.BASE_URL.',
        )

    def handle(self, *args, **options):
        # La limpieza va primero y por fuera de todo lo demás: no necesita el
        # motor de PDF (justo lo que suele estar roto cuando hay que purgar) y
        # nunca debe quedar bloqueada por el opt-in de escritura.
        if options['purge_demo']:
            self._purge_demo()
            return

        if not options['invoice_uuid'] and not options['demo']:
            raise CommandError('Pasá el UUID de una factura o usá --demo.')

        # Guardián de escritura: `--demo` crea filas reales en la base de
        # desarrollo. Sin este opt-in explícito no se toca nada.
        if options['demo'] and not options['escribir_en_dev']:
            raise CommandError(
                'No se creó ni encoló nada.\n\n'
                '--demo escribe clientes, facturas y usuarios REALES en la base de '
                'desarrollo.\n'
                'Si querés probarlo, agregá el opt-in explícito:\n\n'
                '    python manage.py send_test_invoice --demo --escribir-en-dev\n\n'
                'Si lo que querés es borrar lo que quedó de una corrida anterior:\n\n'
                '    python manage.py send_test_invoice --purge-demo'
            )

        # El renderizador se chequea antes de tocar la base: es una dependencia del
        # sistema, no de la factura. Al revés, un `--demo` en una máquina sin la
        # pila de Pango/Harfbuzz deja datos creados que no va a poder usar.
        self._preflight_renderer()

        invoices = (
            self._build_demo_invoices(options['email'])
            if options['demo']
            else [self._get_invoice(options['invoice_uuid'])]
        )

        base_url = options['base_url'] or getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000/')

        for invoice in invoices:
            self._preflight_customer(invoice)
        self._report_backend()

        # Encolar deja trabajo para un worker que no está corriendo: la tarea
        # queda viva en la cola compartida, y si el comando falla o el purge no
        # la alcanza, el `Invoice.objects.get()` de esa tarea revienta después
        # con tres reintentos y backoff. Por defecto el demo ejecuta la tarea acá
        # mismo (mismo PDF, mismo correo, cero residuo) y encolar es opt-in.
        if options['encolar'] and not options['now']:
            for invoice in invoices:
                self._enqueue(invoice, base_url)
        else:
            for invoice in invoices:
                self._run_now(invoice, base_url)

        if options['demo']:
            self.stdout.write(
                self.style.WARNING(
                    'Estos datos son REALES y quedaron en la base de desarrollo.\n'
                    'Cuando termines de mirarlos, borralos con:\n\n'
                    '    python manage.py send_test_invoice --purge-demo'
                )
            )

    # --- datos -------------------------------------------------------------

    def _get_invoice(self, invoice_uuid):
        try:
            invoice = Invoice.objects.get(uuid=invoice_uuid)
        except (Invoice.DoesNotExist, ValueError, TypeError) as exc:
            raise CommandError(f'No existe una factura con uuid={invoice_uuid!r}.') from exc
        self.stdout.write(f'Factura {invoice.number} ({invoice.uuid})')
        return invoice

    def _next_demo_number(self):
        """Siguiente `DEMO-XXXX` libre. Cuenta sobre el total real de filas, no
        sobre las activas: `--purge-demo` borra en duro y el conteo vuelve a cero."""
        numero = ''
        contador = Invoice.objects.count() + 1
        while not numero:
            candidato = f'{DEMO_PREFIX}{contador:04d}'
            if not Invoice.objects.filter(number=candidato).exists():
                numero = candidato
            contador += 1
        return numero

    def _build_demo_invoices(self, email):
        """Un cliente de cada tipo, con su servicio, suscripción y contrato.

        El PDF imprime un bloque distinto según `client_type`, así que un demo con
        un solo tipo deja sin probar la mitad del template.
        """
        user_model = get_user_model()

        # Un servicio compartido por los dos clientes: el bloque del ejecutor es
        # el mismo, lo que cambia es el del cliente.
        user_juridica, _ = user_model.objects.get_or_create(
            username=f'{DEMO_USERNAME_PREFIX}_juridica',
            defaults={
                'email': email,
                'first_name': 'Empresa',
                'last_name': 'Demo',
            },
        )
        self._sync_email(user_juridica, email)

        customer_juridica = self._demo_customer(
            user_juridica,
            client_type=Customer.ClientType.JURIDICA,
            company_name='Empresa de prueba',
            reeup='123.4.5678',
            nit='12345678901',
            account='9001000000000001',
            agency_bank='Banco de Demo',
            identity_document=None,
        )

        user_natural, _ = user_model.objects.get_or_create(
            username=f'{DEMO_USERNAME_PREFIX}_natural',
            defaults={
                'email': email,
                'first_name': 'Cliente',
                'last_name': 'Natural Demo',
            },
        )
        self._sync_email(user_natural, email)

        customer_natural = self._demo_customer(
            user_natural,
            client_type=Customer.ClientType.NATURAL,
            company_name=None,
            reeup=None,
            nit=None,
            account='9001000000000002',
            agency_bank=None,
            identity_document=DEMO_NATURAL_IDENTITY_DOCUMENT,
        )

        service, _ = Service.objects.get_or_create(
            code=f'{DEMO_PREFIX}SERV',
            defaults={
                'user': user_juridica,
                'title': 'Servicio meteorológico de prueba',
                'summary': 'Servicio de prueba para ejercitar el PDF de la factura.',
                'service_type': Service.COMMERCIAL,
                'price': Decimal('100.00'),
            },
        )

        invoices = []
        for customer in (customer_juridica, customer_natural):
            subscription = ServiceSubscription.objects.create(
                customer=customer,
                service=service,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=30),
                payment_status='paid',
                payment_method='transfer',
            )
            # Sin contrato el bloque del ejecutor sale con los tres campos vacíos:
            # el demo lo crea justamente para que salgan llenos.
            Contract.objects.create(
                subscription=subscription,
                number=f'{DEMO_PREFIX}CONT-{len(invoices) + 1:04d}',
                date=timezone.now().date(),
                commercial_registry=f'RC-DEMO-{len(invoices) + 1:04d}',
            )

            invoice = Invoice.objects.create(
                customer=customer,
                subscription=subscription,
                number=self._next_demo_number(),
                amount=Decimal('100.00'),
            )
            InvoiceItem.objects.create(
                invoice=invoice,
                subscription=subscription,
                codigo=f'{DEMO_PREFIX}ITEM',
                descripcion='Servicio meteorológico de prueba',
                cantidad=Decimal('1'),
                unidad_medida='U',
                precio=Decimal('100.00'),
            )
            invoices.append(invoice)
            self.stdout.write(
                self.style.WARNING(
                    f'Datos de prueba creados: factura {invoice.number} ({invoice.uuid}) '
                    f'para {customer.client_type}'
                )
            )
        return invoices

    def _sync_email(self, user, email):
        """El correo se actualiza siempre: si el usuario ya existe de una corrida
        anterior, se manda al destino de esta corrida y no al de la anterior."""
        if user.email != email:
            user.email = email
            user.save(update_fields=['email'])

    def _demo_customer(self, user, **defaults):
        defaults.update(
            {
                'phone': '+53 00000000',
                'address': 'Calle Demo 123, Camagüey',
            }
        )
        customer, _ = Customer.objects.get_or_create(user=user, defaults=defaults)
        return customer

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

    # --- limpieza ----------------------------------------------------------

    def _demo_users(self):
        """Usuarios del demo, nunca un staff ni un superuser.

        El filtro va en la consulta y no después: un `--purge-demo` mal orientado
        no puede terminar borrando el `admin` con el que se entra a la base.
        """
        return get_user_model().objects.filter(
            username__startswith=DEMO_USERNAME_PREFIX, is_staff=False, is_superuser=False
        )

    def _demo_invoices(self, demo_customers):
        """Facturas `DEMO-*` del demo, más las que quedaron sin cliente.

        El prefijo lo reserva este comando, pero el filtro se acota igual a las
        facturas de los clientes del demo o a las huérfanas: un `DEMO-*` mal
        puesto sobre una factura verdadera no se borra por accidente.
        """
        return Invoice.objects.filter(
            Q(number__startswith=DEMO_PREFIX)
            & (Q(customer__in=demo_customers) | Q(customer__isnull=True))
        )

    def _delete_invoice_files(self, invoices):
        """Borra los PDF del disco, uno por uno y solo dentro de MEDIA_ROOT.

        Va antes que el borrado en base: `hard_delete()` no pasa por
        `_cleanup_files()`, así que si el orden fuera al revés los archivos
        quedarían huérfanos sin forma de saber a qué factura pertenecían.
        """
        root = Path(settings.MEDIA_ROOT).resolve()
        borrados = 0
        for invoice in invoices:
            if not invoice.pdf or not invoice.pdf.name:
                continue
            ruta = Path(invoice.pdf.storage.path(invoice.pdf.name)).resolve()
            if root not in ruta.parents:
                self.stderr.write(
                    self.style.WARNING(
                        f'  [aviso] no se borra {ruta}: está fuera de MEDIA_ROOT ({root})'
                    )
                )
                continue
            if not ruta.exists():
                continue
            invoice.pdf.storage.delete(invoice.pdf.name)
            borrados += 1
            # La carpeta `pdf/invoice/` queda vacía y sin uso; se va si se puede.
            if ruta.parent != root:
                with contextlib.suppress(OSError):
                    ruta.parent.rmdir()
        return borrados

    def _purge_demo_tasks(self, invoices):
        """Saca de la cola de Huey las tareas que el demo dejó pendientes.

        Con `--demo` sin `--encolar` esto no tiene nada que borrar (la tarea corrió
        en el proceso). Queda para cuando alguien prueba el camino del worker a
        propósito: la tarea hace `Invoice.objects.get(uuid=...)` sin tolerar
        `DoesNotExist`, así que si el purge borrara las facturas y dejara las
        tareas, el próximo arranque de `run_huey.sh` se comería un
        `DoesNotExist` por cada una, con tres reintentos y backoff.

        Huey no expone una API para borrar una tarea agendada puntual
        (`flush_schedule()` vacía la cola entera, incluido el trabajo real de
        quien esté usando la base), y no todos los backends admiten el SQL crudo
        que hace falta. Donde no se puede, avisa en vez de fingir que limpió.
        """
        from config.huey import huey

        uuids = {str(invoice.uuid) for invoice in invoices}
        if not uuids:
            return 0

        storage = huey.storage
        if not (hasattr(storage, 'sql') and hasattr(storage, 'table_task')):
            self.stderr.write(
                self.style.WARNING(
                    f'  [aviso] el backend de Huey ({type(storage).__name__}) no permite '
                    'borrar tareas puntuales: si usaste --encolar, sacá a mano lo que '
                    'quede en la cola.'
                )
            )
            return 0

        borrados = 0
        # Ojo: `storage.table_task`/`table_sched` de Huey son el *DDL* de la tabla
        # ("create table if not exists task (...)"), no el nombre. Los nombres
        # van acá y son 'task' (pendientes) y 'schedule' (agendadas).
        for tabla in ('task', 'schedule'):
            filas = storage.sql(
                f'select id, data from {tabla} where queue = ?',  # noqa: S608
                (huey.name,),
                results=True,
            )
            idlistas = []
            for fila_id, data in filas:
                try:
                    msg = huey.deserialize_task(data)
                except Exception:  # noqa: BLE001 - un blob ajeno no es motivo para abortar
                    continue
                if not msg.name.endswith(DEMO_TASK_NAME_SUFFIX) or not msg.args:
                    continue
                # El UUID de la factura del demo es lo que decide: una tarea
                # cuya factura se va a borrar es una tarea propia, diga lo que
                # diga su nombre.
                if str(msg.args[0]) in uuids:
                    idlistas.append(fila_id)
                    # El resultado que el worker guarde de esta tarea es basura
                    # también: se borra acá, antes de que la fila desaparezca.
                    storage.delete_data(msg.id)
            if idlistas:
                storage.sql(
                    f'delete from {tabla} where id in ({",".join("?" * len(idlistas))})',  # noqa: S608
                    idlistas,
                    commit=True,
                )
                borrados += len(idlistas)

        if borrados:
            self.stdout.write(f'  [ok] {borrados} tarea(s) del demo sacadas de la cola de Huey')
        return borrados

    def _demo_services(self, customers):
        """Servicios `DEMO-*` del demo.

        Igual que con las facturas, el prefijo se acota: solo entra el servicio
        que las suscripciones del demo usan o el que no tiene ninguna
        suscripción, así que un `DEMO-*` real y en uso no se borra por el código
        solo.
        """
        demo_subs = ServiceSubscription.objects.filter(customer__in=customers)
        return Service.objects.filter(code__startswith=DEMO_PREFIX).filter(
            Q(servicesubscription__in=demo_subs) | Q(servicesubscription__isnull=True)
        )

    def _purge_demo(self):
        users = list(self._demo_users())
        customers = list(Customer.objects.filter(user__in=users))
        invoices = list(self._demo_invoices(customers))
        services = list(self._demo_services(customers))

        if not (users or customers or invoices or services):
            self.stdout.write('No hay datos del demo para borrar.')
            return

        pdfs = self._delete_invoice_files(invoices)
        # La cola va primero que la base: la tarea busca la factura por UUID, así
        # que para cuando el worker la encuentre ya no tiene que existir.
        tasks = self._purge_demo_tasks(invoices)

        # Todo en una transacción: o no queda nada del demo, o queda todo.
        with transaction.atomic():
            # `hard_delete()` y no `delete()`: `Customer`/`Invoice` son de borrado
            # lógico y un `delete()` los dejaría como `record_active=False`, que
            # es exactamente la basura que hay que sacar de la base de desarrollo.
            for invoice in invoices:
                invoice.hard_delete()
            for customer in customers:
                # El hard_delete del cliente se lleva sus suscripciones, sus
                # contratos y sus facturas huérfanas por cascada.
                customer.hard_delete()
            for service in services:
                service.hard_delete()
            for user in users:
                user.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Datos del demo borrados: {len(users)} usuario(s), {len(customers)} cliente(s), '
                f'{len(invoices)} factura(s), {len(services)} servicio(s), {pdfs} PDF(s), '
                f'{tasks} tarea(s) de la cola.'
            )
        )

    # --- preflight ---------------------------------------------------------

    def _preflight_renderer(self):
        try:
            require_pdf_renderer()
        except RuntimeError as exc:
            self.stdout.write(self.style.ERROR('  [falta] WeasyPrint'))
            raise CommandError(
                f'Preflight fallido:\n\n{exc}\n\nNo se creó ni encoló nada.'
            ) from exc
        self.stdout.write(self.style.SUCCESS('  [ok] WeasyPrint genera PDF'))

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
            # La tarea propaga el fallo de cada paso, así que acá ya se sabe
            # cuál fue. Antes el correo se reportaba como tarea exitosa y
            # este comando no decía nada.
            invoice.refresh_from_db()
            paso = 'PDF' if invoice.pdf_status == Invoice.PdfStatus.FAILED else 'correo'
            detalle = invoice.pdf_error if paso == 'PDF' else invoice.email_error
            self.stderr.write(
                self.style.ERROR(
                    f'Falló el paso "{paso}" de la factura {invoice.number}.\n'
                    f'  pdf_status={invoice.pdf_status}  email_status={invoice.email_status}\n'
                    f'  detalle: {detalle or "(sin detalle)"}\n'
                    f'  error: {type(exc).__name__}: {exc}'
                )
            )
            raise CommandError(f'La tarea falló en el paso "{paso}".') from exc

        invoice.refresh_from_db()
        recipient = self._resolve_customer(invoice).user.email
        self.stdout.write(
            self.style.SUCCESS(
                f'Factura {invoice.number}: PDF {invoice.pdf_status} y correo enviado a {recipient}'
            )
        )
