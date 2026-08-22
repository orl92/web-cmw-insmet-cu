# Tasks — 004-monitoreo-tareas

Phased, completable in one session each. Anchored to current code (see `design.md`).

## Phase 1 — Data model

- [ ] 1.1 Add `TaskExecutionLog` model to `apps/core/models.py` (fields, choices, indexes,
      `default_permissions = ()` + 4 Spanish custom perms, NO soft delete) — per `design.md` §3.
- [ ] 1.2 Generate migration: `python manage.py makemigrations apps.core` (not versioned).
- [ ] 1.3 Register `TaskExecutionLog` in `apps/core/admin.py` as read-only admin — per `design.md` §6.

## Phase 2 — Signal capture

- [ ] 2.1 Implement `_safe_args(task)` and `_tb(exc)` sanitizing helpers in `apps/core/apps.py`.
- [ ] 2.2 Register `SIGNAL_ENQUEUED`, `SIGNAL_EXECUTING`, `SIGNAL_COMPLETE`, `SIGNAL_RETRYING`,
      `SIGNAL_ERROR` handlers in `apps/core/apps.py` `ready()` (replacing the stub at
      `apps/core/apps.py:9`) — per `design.md` §4.
- [ ] 2.3 Ensure handlers never raise into the worker (wrap bodies in `try/except` logging only).

## Phase 3 — Retry & failure visibility

- [ ] 3.1 Add `retries=3, retry_delay=30, retry_backoff=True` to `generate_invoice_pdf_and_email_task`
      (`apps/core/tasks.py:11`).
- [ ] 3.2 Add same retry config to `send_email_task` (`apps/core/tasks.py:34`).
- [ ] 3.3 Remove the `try/except Exception` swallow at `apps/core/tasks.py:59-62` so failures
      propagate to `SIGNAL_ERROR` and retry.

## Phase 4 — Dashboard monitoring view

- [ ] 4.1 Add `TaskMonitoringView` (superuser-only, DataTables) in
      `apps/dashboard/views/dashboard/dashboard.py` — per `design.md` §7.
- [ ] 4.2 Add `path('tasks/', ..., name='tasks')` to `apps/dashboard/urls.py` (`app_name='dashboard'`).
- [ ] 4.3 Create `apps/dashboard/templates/pages/dashboard/tasks.html` (Tabler): status badges,
      stale-queue (>5 min) red banner, error-count banner, expandable traceback.

## Phase 5 — Tests & verification

- [ ] 5.1 Add `apps/core/tests/test_task_monitoring.py`: enqueue→SUCCESS log, forced failure→ERROR
      log + traceback, retry config assertions, no-swallow assertion — per `design.md` §8.
- [ ] 5.2 Run `python manage.py check && python manage.py test apps.core`; fix failures.
- [ ] 5.3 Run `djlint . --reformat --check` and `djlint . --lint` on the new template; `ruff` clean.
