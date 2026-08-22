# Proposal

## Intent

Add observability for asynchronous Huey task execution in `web-cmw-insmet-cu`: capture each
task's lifecycle (enqueued, executing, success, failure, retry), surface failures and retries
with tracebacks, and alert when a task is stale in the queue or fails. This replaces the current
"fire-and-forget" behavior where task outcomes are invisible until a user reports a missing
invoice PDF or an undelivered email.

Preserved intent from the legacy change `004-monitoreo-tareas`: monitor async Huey tasks and
(scheduled/periodic) jobs — status, failures, retries, and alerting.

## Scope In

- Capture execution state for the **two** existing Huey task types:
  - `generate_invoice_pdf_and_email_task` — `apps/core/tasks.py:11`, enqueued by invoice
    create/update at `apps/commercial/views/invoices.py:210` and `:286`.
  - `send_email_task` — `apps/core/tasks.py:34`, enqueued by `mail_send`
    (`apps/core/utils.py:100-132`) on Warning/WeatherReport create/update
    (`apps/meteo/views/warning.py:151,216`; `apps/meteo/views/weather_report.py:212,278`).
- Persist a `TaskExecutionLog` record per task execution in the primary database, queryable from
  Django admin and a new Dashboard view.
- Wire Huey signal handlers in `apps/core/apps.py` `ready()` (currently a stub at
  `apps/core/apps.py:9`) using huey 3.3.4 `huey.signal(...)` with constants `SIGNAL_ENQUEUED`,
  `SIGNAL_EXECUTING`, `SIGNAL_COMPLETE`, `SIGNAL_ERROR`, `SIGNAL_RETRYING` (API verified in the
  active venv).
- Add retry semantics to both tasks (`retries`, `retry_delay`, `retry_backoff`) and fix
  `send_email_task` so it no longer swallows exceptions (`apps/core/tasks.py:59-62`); today
  failures are logged and discarded, making them invisible and non-retryable.
- Superuser-only Dashboard monitoring view with status, failure tracebacks, retry count, and a
  visual alert for tasks stuck in the queue beyond a 5-minute threshold.
- Unit tests for the logging model, signal handlers, and retry behavior.

## Scope Out

- **Migrating `SqliteHuey` to `huey.contrib.djhuey`.** The legacy proposal assumed `djhuey`; the
  current code uses a raw `SqliteHuey` instance (`config/huey.py:7-10`) and `requirements.txt:78`
  lists only `huey` (3.3.4 installed). This change keeps the existing integration and layers
  monitoring on top. Rationale: avoid an unnecessary, risky infra migration; the same observability
  goal is reachable with signals.
- **Implementing periodic/scheduled Huey jobs.** Investigation found **zero** `periodic_task` /
  `crontab` definitions in the codebase (grep returned 0 matches). The design stores `task_id` and
  `task_name` so periodic tasks can be monitored later without a schema change, but building
  scheduled jobs is a separate concern.
- **External alerting channels** (email/Slack) on failure. The `SIGNAL_ERROR` handler records the
  failure and emits a Django log; wiring to `mail_send` / `EmailRecipientList` is left to a future
  change to keep this one minimal.
- **Replacing the file-based worker log** at `run_huey.sh:9`
  (`--logfile=logs/huey.log --verbose`). Both can coexist.

## Approach

Anchored to current code:

1. **Keep the broker as-is.** `config/huey.py:7-10` defines
   `SqliteHuey('web-cmw', filename=BASE_DIR / 'huey.db')`. No change to storage.
2. **New model `TaskExecutionLog`** in `apps/core/models.py`. It is auxiliary/transactional, so it
   MUST NOT use soft delete (per `AGENTS.md` convention for auxiliary/transactional models). Plain
   `models.Model` with `default_permissions = ()` + the 4 custom Spanish permissions
   (`view_/add_/change_/delete_taskExecutionLog`). Fields:
   - `task_id` (CharField, Huey task id, indexed)
   - `task_name` (CharField)
   - `status` (CharField, choices: ENQUEUED / EXECUTING / SUCCESS / ERROR / RETRYING / REVOKED)
   - `enqueued_at`, `started_at`, `finished_at` (DateTimeField, nullable)
   - `attempts` (PositiveIntegerField, default 0)
   - `error_message` (TextField, truncated)
   - `traceback` (TextField, truncated)
   - `args_repr` (CharField, truncated, no secrets — never log `recipients`/`html_message` bodies)
   - `Meta.ordering = ['-enqueued_at']`; indexes on `(status, enqueued_at)` for the stale-queue query.
3. **Signal handlers** registered in `apps/core/apps.py` `ready()` (replace the stub at
   `apps/core/apps.py:9`). Use `@huey.signal(SIGNAL_ENQUEUED)`, `SIGNAL_EXECUTING`,
   `SIGNAL_COMPLETE`, `SIGNAL_ERROR`, `SIGNAL_RETRYING`. Each handler upserts the `TaskExecutionLog`
   row keyed by `task.id` (create on ENQUEUED, update on the rest). On `SIGNAL_ERROR` /
   `SIGNAL_RETRYING`: set status, store the handler's `exc` message + traceback, increment
   `attempts`, and `logger.error(...)`. API confirmed in venv: `Huey.signal(*signals)` and
   `Huey.task(retries=, retry_delay=, retry_backoff=, context=)` exist in huey 3.3.4.
4. **Retries** on the two tasks: `generate_invoice_pdf_and_email_task` (`apps/core/tasks.py:11`)
   and `send_email_task` (`apps/core/tasks.py:34`) get `retries=3, retry_delay=30,
   retry_backoff=True`. Remove the `try/except` swallow in `send_email_task`
   (`apps/core/tasks.py:59-62`) and let exceptions propagate so Huey emits `SIGNAL_ERROR` and
   retries.
5. **Admin** `apps/core/admin.py`: `admin.register(TaskExecutionLog)` with
   `list_display=(task_name, status, attempts, enqueued_at, finished_at)`,
   `readonly_fields` for all fields, `list_filter=(status,)`.
6. **Dashboard view** `TaskMonitoringView` in `apps/dashboard/views/dashboard/dashboard.py`, reusing
   the `UserPassesTestMixin` + `is_superuser` guard from `DashboardView` in the same file. Use
   DataTables (per `AGENTS.md`: DataTables loads all rows, client pagination) for the operational
   feed. Template `apps/dashboard/templates/pages/dashboard/tasks.html` (Tabler cards + badges).
   URL `path('tasks/', TaskMonitoringView.as_view(), name='tasks')` in `apps/dashboard/urls.py`
   (`app_name='dashboard'`).
   - **Stale-queue alert:** rows with `status='ENQUEUED' and enqueued_at < now - 5min` render a red
     banner + row badges. This grounds the legacy "cola > 5 min" criterion in real captured data.
   - **Failure alert:** rows with `status='ERROR'` render a warning badge and an expandable
     traceback.
7. **Tests** `apps/core/tests/test_task_monitoring.py`: run tasks via huey immediate mode (or
   `call_local`, as in `apps/core/tests/test_tasks.py:18`) to assert a `TaskExecutionLog` is
   created/updated; assert a forced exception yields `status='ERROR'` with traceback captured;
   assert retry config via `task.retries`.

## Acceptance Criteria

- [ ] `TaskExecutionLog` model exists in `apps/core/models.py`, is migrated, queryable, with
      `status` choices and **no** soft delete.
- [ ] A `TaskExecutionLog` row is created on task enqueue and updated through executing →
      success/error/retrying, keyed by `task.id`.
- [ ] Failures store `error_message` + `traceback` and are visible in admin and the Dashboard view.
- [ ] Both tasks carry retry config (`retries >= 1`); `send_email_task` no longer swallows
      exceptions.
- [ ] Dashboard `tasks` view is superuser-only and shows status, attempts, failures, and a visual
      alert for tasks enqueued > 5 min without starting.
- [ ] Unit tests pass: `python manage.py test apps.core`.

## Rollback

All changes are additive (new model + migration, new signal handlers, new view/URL/template,
expanded task decorators). Rollback = revert the commits and `migrate apps.core zero` for the new
model migration (or simply drop the table via the reversed migration), then remove the URL/template.
No change to `config/huey.py` broker or `run_huey.sh`, so the worker keeps functioning. If retries
cause duplicate sends on partial failure, set `retries=0` via a one-line revert of the decorator
args.
