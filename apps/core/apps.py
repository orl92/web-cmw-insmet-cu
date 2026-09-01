import logging
import traceback

from django.apps import AppConfig
from django.db.models import F
from django.utils import timezone
from huey import signals as huey_signals

from config.huey import huey

logger = logging.getLogger(__name__)


def _safe_args(task):
    """Truncated, sanitized repr of task args.

    Only the first positional arg is shown and everything else is omitted so
    that sensitive values (recipients, email bodies, attachment contents) are
    never persisted to the execution log.
    """
    try:
        args = getattr(task, 'args', None) or ()
        if not args:
            return f'{task.name}()'[:512]
        head = repr(args[0])[:200]
        rest = ', (...) omitido' if len(args) > 1 else ''
        return f'{task.name}({head}{rest})'[:512]
    except Exception:
        return ''


def _tb(exc):
    """Truncated traceback string for an exception, or empty when none."""
    if exc is None:
        return ''
    try:
        return ''.join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )[:4000]
    except Exception:
        return str(exc)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Configuración'

    def ready(self):
        from pathlib import Path

        from django.conf import settings

        Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)

        from apps.core.models import TaskExecutionLog

        @huey.signal(huey_signals.SIGNAL_ENQUEUED)
        def on_enqueued(signal, task):
            try:
                TaskExecutionLog.objects.update_or_create(
                    task_id=task.id,
                    defaults={
                        'task_name': task.name,
                        'status': TaskExecutionLog.STATUS_ENQUEUED,
                        'enqueued_at': timezone.now(),
                        'args_repr': _safe_args(task),
                    },
                )
            except Exception:
                logger.exception('on_enqueued: fallo al registrar la tarea %s', task.id)

        @huey.signal(huey_signals.SIGNAL_EXECUTING)
        def on_executing(signal, task):
            try:
                TaskExecutionLog.objects.filter(task_id=task.id).update(
                    status=TaskExecutionLog.STATUS_EXECUTING,
                    started_at=timezone.now(),
                )
            except Exception:
                logger.exception('on_executing: fallo al actualizar %s', task.id)

        @huey.signal(huey_signals.SIGNAL_COMPLETE)
        def on_complete(signal, task):
            try:
                TaskExecutionLog.objects.filter(task_id=task.id).update(
                    status=TaskExecutionLog.STATUS_SUCCESS,
                    finished_at=timezone.now(),
                )
            except Exception:
                logger.exception('on_complete: fallo al actualizar %s', task.id)

        @huey.signal(huey_signals.SIGNAL_RETRYING)
        def on_retrying(signal, task, exc=None):
            try:
                # Huey emits SIGNAL_RETRYING without the exception, so we must
                # preserve the error_message/traceback that on_error already
                # stored for the failed attempt instead of overwriting them.
                update = {
                    'status': TaskExecutionLog.STATUS_RETRYING,
                    'attempts': F('attempts') + 1,
                    'finished_at': timezone.now(),
                }
                if exc is not None:
                    update['error_message'] = str(exc)[:2000]
                    update['traceback'] = _tb(exc)
                TaskExecutionLog.objects.filter(task_id=task.id).update(**update)
            except Exception:
                logger.exception('on_retrying: fallo al actualizar %s', task.id)

        @huey.signal(huey_signals.SIGNAL_ERROR)
        def on_error(signal, task, exc=None):
            try:
                TaskExecutionLog.objects.filter(task_id=task.id).update(
                    status=TaskExecutionLog.STATUS_ERROR,
                    attempts=F('attempts') + 1,
                    error_message=str(exc)[:2000],
                    traceback=_tb(exc),
                    finished_at=timezone.now(),
                )
                logger.error('Huey task %s failed: %s', task.name, exc)
            except Exception:
                logger.exception('on_error: fallo al registrar el error de %s', task.id)
