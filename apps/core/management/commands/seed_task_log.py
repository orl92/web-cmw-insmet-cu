"""Rellena TaskExecutionLog con datos de simulación para probar la tabla de
monitoreo de tareas del dashboard (estados, banners, botones y truncado).

Uso:
    python manage.py seed_task_log [--flush]

--flush  elimina los registros de TaskExecutionLog antes de insertar los demo.
"""

import json
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import TaskExecutionLog

UUID = '00000000-0000-0000-0000-000000000000'


def _traceback():
    return (
        'Traceback (most recent call last):\n'
        '  File "/app/apps/core/tasks.py", line 42, in '
        'generate_invoice_pdf_and_email_task\n'
        '    invoice = Invoice.objects.get(uuid=payload["invoice_uuid"])\n'
        '  File "..../models/query.py", line 544, in get\n'
        '    raise self.model.DoesNotExist(\n'
        'apps.commercial.models.DoesNotExist: '
        'Invoice matching query does not exist.\n'
    )


class Command(BaseCommand):
    help = 'Rellena TaskExecutionLog con datos de simulación para probar la tabla de monitoreo.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Borra los registros existentes antes de insertar los datos demo.',
        )

    def handle(self, *args, **options):
        if options['flush']:
            deleted, _ = TaskExecutionLog.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Registros eliminados: {deleted}'))

        now = timezone.now()
        dw = TaskExecutionLog

        rows = [
            # ENQUEUED reciente: intentos 0, sin Inicio/Fin -> muestra "—".
            dict(
                task_id='demo-reciente-1',
                task_name='send_email_task',
                status=dw.STATUS_ENQUEUED,
                enqueued_at=now - timedelta(minutes=1),
                attempts=0,
                args_repr=(
                    "send_email_task('Asunto: aviso', "
                    "recipients=['cliente@empresa.cu'], (...) omitido)"
                ),
            ),
            # ENQUEUED viejo: dispara el banner alert-danger (trabajador caído).
            dict(
                task_id='demo-stale-1',
                task_name='generate_invoice_pdf_and_email_task',
                status=dw.STATUS_ENQUEUED,
                enqueued_at=now - timedelta(minutes=45),
                attempts=0,
                args_repr=f"generate_invoice_pdf_and_email_task({UUID!r}, 'https://insmet.cu')",
                # Retryable: permite reencolar aunque aún no inicie.
                func_name='apps.core.tasks.generate_invoice_pdf_and_email_task',
                func_args=json.dumps({'args': [UUID, 'https://insmet.cu'], 'kwargs': {}}),
            ),
            # EXECUTING: Inicio sí, Fin no.
            dict(
                task_id='demo-ejecutando-1',
                task_name='send_email_task',
                status=dw.STATUS_EXECUTING,
                enqueued_at=now - timedelta(minutes=3),
                started_at=now - timedelta(seconds=20),
                attempts=1,
                args_repr=(
                    "send_email_task('Boletín semanal', recipients=['a@x.cu'], (...) omitido)"
                ),
            ),
            # SUCCESS completo.
            dict(
                task_id='demo-ok-1',
                task_name='send_email_task',
                status=dw.STATUS_SUCCESS,
                enqueued_at=now - timedelta(days=1, hours=1),
                started_at=now - timedelta(days=1, hours=1, minutes=-5),
                finished_at=now - timedelta(days=1, hours=1),
                attempts=1,
                args_repr=(
                    "send_email_task('Confirmación de pago', "
                    "recipients=['cli@dom.cu'], (...) omitido)"
                ),
            ),
            # ERROR retryable: con func_args -> botones Reintentar + traceback + eliminar.
            dict(
                task_id='demo-error-retry-1',
                task_name='generate_invoice_pdf_and_email_task',
                status=dw.STATUS_ERROR,
                enqueued_at=now - timedelta(hours=2),
                started_at=now - timedelta(hours=2, minutes=-3),
                finished_at=now - timedelta(hours=2),
                attempts=3,
                error_message='Invoice matching query does not exist.',
                traceback=_traceback(),
                args_repr=f"generate_invoice_pdf_and_email_task({UUID!r}, 'https://insmet.cu')",
                func_name='apps.core.tasks.generate_invoice_pdf_and_email_task',
                func_args=json.dumps({'args': [UUID, 'https://insmet.cu'], 'kwargs': {}}),
            ),
            # ERROR no-retryable: send_email_task sin func_args -> solo traceback + eliminar.
            dict(
                task_id='demo-error-mail-1',
                task_name='send_email_task',
                status=dw.STATUS_ERROR,
                enqueued_at=now - timedelta(hours=5),
                started_at=now - timedelta(hours=5, minutes=-2),
                finished_at=now - timedelta(hours=5),
                attempts=2,
                error_message='SMTP connection refused',
                traceback=(
                    'Traceback (most recent call last):\n'
                    '  File "apps/core/tasks.py", line 30, in send_email_task\n'
                    '    connection.send_messages([message])\n'
                    "smtplib.SMTPConnectError: (111, 'Connection refused')\n"
                ),
                args_repr=(
                    "send_email_task('Aviso de factura', recipients=['x@y.cu'], (...) omitido)"
                ),
            ),
            # RETRYING: intentos > 1 (Huey reintentando automáticamente).
            dict(
                task_id='demo-retry-1',
                task_name='send_email_task',
                status=dw.STATUS_RETRYING,
                enqueued_at=now - timedelta(minutes=30),
                started_at=now - timedelta(minutes=30, seconds=10),
                attempts=2,
                error_message='Timeout SMTP (reintentando)',
                args_repr="send_email_task('Factura #0012', recipients=['f@c.cu'], (...) omitido)",
            ),
            # REVOKED.
            dict(
                task_id='demo-revocada-1',
                task_name='send_email_task',
                status=dw.STATUS_REVOKED,
                enqueued_at=now - timedelta(days=2),
                attempts=0,
                args_repr="send_email_task('Legado', recipients=['old@go.cu'], (...) omitido)",
            ),
            # SUCCESS con args largas: prueba el truncado a 45 chars con tooltip completo.
            dict(
                task_id='demo-ok-largo-1',
                task_name='send_email_task',
                status=dw.STATUS_SUCCESS,
                enqueued_at=now - timedelta(days=3),
                started_at=now - timedelta(days=3),
                finished_at=now - timedelta(days=3, hours=-1),
                attempts=1,
                args_repr=(
                    "send_email_task('Boletín meteorológico semanal N° 2026-09 con muchos "
                    "detalles y un asunto bastante extenso para probar el truncado', "
                    "recipients=['destinatario.largo@dominio.ejemplo.cu', "
                    "'otro.destinatario@dominio.cu'], (...) omitido)"
                ),
            ),
            # SUCCESS con args vacía: la celda muestra "—".
            dict(
                task_id='demo-vacio-1',
                task_name='send_email_task',
                status=dw.STATUS_SUCCESS,
                enqueued_at=now - timedelta(days=4),
                started_at=now - timedelta(days=4),
                finished_at=now - timedelta(days=4, hours=-1),
                attempts=1,
                args_repr='',
            ),
        ]

        created = TaskExecutionLog.objects.bulk_create([TaskExecutionLog(**r) for r in rows])

        self.stdout.write(
            self.style.SUCCESS(
                f'Se insertaron {len(created)} registros de simulación (TaskExecutionLog).'
            )
        )
        self.stdout.write(
            'Estados cubiertos: ENQUEUED (reciente + stale), EXECUTING, SUCCESS, '
            'ERROR (retryable + no-retryable), RETRYING, REVOKED, args largas y vacías.'
        )
