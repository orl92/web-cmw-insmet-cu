# Design — Task Monitoring & Observability (004-monitoreo-tareas)

## 1. Context & Current Reality (verified)

- **Broker:** `SqliteHuey('web-cmw', filename=BASE_DIR / 'huey.db')` at `config/huey.py:7-10`.
  Not `djhuey` — a raw Huey instance. `requirements.txt:78` lists only `huey`.
- **Worker:** `run_huey.sh:9` runs `huey_consumer config.huey.huey --logfile=logs/huey.log --verbose`.
  Logs go to a file; no structured/queryable state.
- **Tasks (only two):**
  - `generate_invoice_pdf_and_email_task(invoice_uuid, site_url)` — `apps/core/tasks.py:11-31`. No
    retries, no try/except; an exception propagates to the worker (Huey marks it errored, but
    nothing records it).
  - `send_email_task(...)` — `apps/core/tasks.py:34-62`. **Swallows exceptions**
    (`apps/core/tasks.py:59-62`: `except Exception as e: logger.error(...)`), so failures are
    invisible and never retried.
- **Enqueue sites:** invoice create/update (`apps/commercial/views/invoices.py:210,286`);
  `mail_send` (`apps/core/utils.py:100-132`) called from `apps/meteo/views/warning.py:151,216` and
  `apps/meteo/views/weather_report.py:212,278`.
- **Signal API (verified in venv, huey 3.3.4):** `Huey.signal(*signals)` decorator; constants in
  `huey.signals`: `SIGNAL_ENQUEUED`, `SIGNAL_EXECUTING`, `SIGNAL_COMPLETE`, `SIGNAL_ERROR`,
  `SIGNAL_RETRYING`, `SIGNAL_REVOKED`, `SIGNAL_LOCKED`, `SIGNAL_TIMEOUT`. `Huey.task(retries=,
  retry_delay=, retry_backoff=, context=)` available. `SIGNAL_ERROR`/`SIGNAL_RETRYING` handlers
  receive `(signal, task, exc)`.
- **No periodic tasks exist** (grep for `periodic_task`/`crontab` returned 0). Monitoring is
  designed to be future-proof via generic `task_id`/`task_name` columns.

## 2. Architecture Decision

Layer observability **on top** of the existing `SqliteHuey` via Huey's signal system, persisting
lifecycle events into a new Django model (`TaskExecutionLog`) in the **primary** database. Rationale:

- **No broker migration.** `djhuey` would require `INSTALLED_APPS` + `HUEY` settings changes and a
  storage swap — risky, and orthogonal to the observability goal. Signals give us the same
  visibility with zero broker change.
- **Primary-DB store (not `huey.db`).** `TaskExecutionLog` is queryable by Django ORM, admin, and
  the Dashboard view without touching the worker's SQLite. Avoids coupling to Huey storage internals
  (`huey.pending()`/`scheduled()` give counts only, not per-task timing).
- **Signals over polling.** Event-driven capture is exact and cheap; polling the broker would add
  latency and load.

## 3. Data Model — `apps/core/models.py`

```python
class TaskExecutionLog(models.Model):
    STATUS_ENQUEUED = 'ENQUEUED'
    STATUS_EXECUTING = 'EXECUTING'
    STATUS_SUCCESS = 'SUCCESS'
    STATUS_ERROR = 'ERROR'
    STATUS_RETRYING = 'RETRYING'
    STATUS_REVOKED = 'REVOKED'
    STATUS_CHOICES = [
        (STATUS_ENQUEUED, 'Enqueued'),
        (STATUS_EXECUTING, 'Executing'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_ERROR, 'Error'),
        (STATUS_RETRYING, 'Retrying'),
        (STATUS_REVOKED, 'Revoked'),
    ]

    task_id = models.CharField(max_length=255, db_index=True)
    task_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ENQUEUED)
    enqueued_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    traceback = models.TextField(blank=True)
    args_repr = models.CharField(max_length=512, blank=True)

    class Meta:
        ordering = ['-enqueued_at']
        indexes = [models.Index(fields=['status', 'enqueued_at'])]
        default_permissions = ()
        permissions = [
            ('view_taskExecutionLog', 'Can view task execution log'),
            ('add_taskExecutionLog', 'Can add task execution log'),
            ('change_taskExecutionLog', 'Can change task execution log'),
            ('delete_taskExecutionLog', 'Can delete task execution log'),
        ]

    def __str__(self):
        return f'{self.task_name} {self.status} ({self.task_id})'
```

Notes:
- **No soft delete** (auxiliary/transactional per `AGENTS.md`).
- `args_repr` is a **truncated, sanitized** repr. Never persist `recipients` lists, email bodies, or
  `html_message`. Build it defensively in the signal handler (e.g. `task.args[:1]` + `'(...)'
  omitted`).
- Migration is generated via `python manage.py makemigrations` (NOT versioned per `AGENTS.md`).

## 4. Signal Handlers — `apps/core/apps.py`

Replace the stub `ready()` (`apps/core/apps.py:9`) with signal registration. Keep handlers resilient
(idempotent upsert by `task.id`; never raise into the worker).

```python
from huey import signals as huey_signals
from apps.core.models import TaskExecutionLog

def _log_for(task):
    log, _ = TaskExecutionLog.objects.get_or_create(
        task_id=task.id,
        defaults={'task_name': task.name, 'enqueued_at': timezone.now()},
    )
    return log

@huey.signal(huey_signals.SIGNAL_ENQUEUED)
def on_enqueued(signal, task):
    TaskExecutionLog.objects.update_or_create(
        task_id=task.id,
        defaults={'task_name': task.name, 'status': TaskExecutionLog.STATUS_ENQUEUED,
                  'enqueued_at': timezone.now(),
                  'args_repr': _safe_args(task)},
    )

@huey.signal(huey_signals.SIGNAL_EXECUTING)
def on_executing(signal, task):
    TaskExecutionLog.objects.filter(task_id=task.id).update(
        status=TaskExecutionLog.STATUS_EXECUTING, started_at=timezone.now())

@huey.signal(huey_signals.SIGNAL_COMPLETE)
def on_complete(signal, task):
    TaskExecutionLog.objects.filter(task_id=task.id).update(
        status=TaskExecutionLog.STATUS_SUCCESS, finished_at=timezone.now())

@huey.signal(huey_signals.SIGNAL_RETRYING)
def on_retrying(signal, task, exc=None):
    TaskExecutionLog.objects.filter(task_id=task.id).update(
        status=TaskExecutionLog.STATUS_RETRYING, attempts=models.F('attempts') + 1,
        error_message=str(exc)[:2000], traceback=_tb(exc), finished_at=timezone.now())

@huey.signal(huey_signals.SIGNAL_ERROR)
def on_error(signal, task, exc=None):
    TaskExecutionLog.objects.filter(task_id=task.id).update(
        status=TaskExecutionLog.STATUS_ERROR, attempts=models.F('attempts') + 1,
        error_message=str(exc)[:2000], traceback=_tb(exc), finished_at=timezone.now())
    logger.error('Huey task %s failed: %s', task.name, exc)
```

`_safe_args(task)` and `_tb(exc)` are helper functions that truncate and sanitize. `SIGNAL_ERROR`
also emits a Django `logger.error` so the existing `logs/huey.log` path still receives the failure.

## 5. Retry + Failure Visibility Fix — `apps/core/tasks.py`

- `generate_invoice_pdf_and_email_task` (`apps/core/tasks.py:11`):
  `@huey.task(retries=3, retry_delay=30, retry_backoff=True)`.
- `send_email_task` (`apps/core/tasks.py:34`): same retry config, and **remove the
  `try/except Exception` swallow** at `apps/core/tasks.py:59-62` so exceptions propagate and trigger
  `SIGNAL_ERROR` + retries. Keep a narrow, explicit guard only for attachment-read I/O if needed,
  but never swallow the `email.send()` failure.

## 6. Admin — `apps/core/admin.py`

```python
@admin.register(TaskExecutionLog)
class TaskExecutionLogAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'status', 'attempts', 'enqueued_at', 'finished_at')
    list_filter = ('status',)
    readonly_fields = [f.name for f in TaskExecutionLog._meta.fields]
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
```

## 7. Dashboard View — `apps/dashboard`

- **View** `TaskMonitoringView` in `apps/dashboard/views/dashboard/dashboard.py`, mirroring
  `DashboardView`'s `UserPassesTestMixin` + `is_superuser` guard. Use DataTables (loads all rows;
  client pagination per `AGENTS.md`). `get_context_data` adds:
  - `executions`: recent `TaskExecutionLog` rows (e.g. last 500 or filtered by `?status=&?range=`).
  - `stale_threshold_minutes = 5`.
  - `stale_count`: `TaskExecutionLog.objects.filter(status=ENQUEUED,
    enqueued_at__lt=now - timedelta(minutes=5)).count()`.
  - `error_count`: `TaskExecutionLog.objects.filter(status=ERROR).count()`.
- **URL** `apps/dashboard/urls.py`: add `path('tasks/', TaskMonitoringView.as_view(), name='tasks')`
  (within `app_name='dashboard'`).
- **Template** `apps/dashboard/templates/pages/dashboard/tasks.html` (Tabler): a red banner when
  `stale_count > 0` or `error_count > 0`; a DataTables table with status badges (color-coded),
  attempts, enqueued/started/finished timestamps, and an expandable traceback column for errors.

## 8. Tests — `apps/core/tests/test_task_monitoring.py`

Use huey immediate execution (set `huey.immediate = True` in the test or call `task.call_local`,
as in `apps/core/tests/test_tasks.py:18`):

- `test_enqueue_creates_log`: enqueue `send_email_task` (locmem backend) → assert a
  `TaskExecutionLog` with `status=SUCCESS` exists for the task id.
- `test_failure_records_error`: a task variant that raises → assert `status=ERROR`, `attempts >= 1`,
  `traceback` non-empty.
- `test_retry_config`: assert `generate_invoice_pdf_and_email_task.retries >= 1` and
  `send_email_task.retries >= 1`.
- `test_send_email_no_swallow`: assert `send_email_task` no longer wraps `email.send()` in a
  bare `except` (code-level assertion or behavioral test that an exception surfaces as ERROR).

Run: `python manage.py test apps.core`.

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Signal handler raises into the worker, breaking tasks | Handlers are read-only upserts; wrap body in `try/except` logging only. |
| Secrets in `args_repr` | `_safe_args` truncates and omits sensitive args (recipients, bodies). |
| Stale-queue false positives if worker is down | Banner is informational only; does not block enqueue. Paired with existing `logs/huey.log`. |
| Duplicate emails on retry | `retry_backoff=True` + bounded `retries=3`; `generate_invoice_pdf_and_email_task` is idempotent (regenerates PDF). Acceptable; reversible by `retries=0`. |
| Per-task signal timing overhead | Upserts are indexed (`task_id`); volume is low (emails/invoices). |
