# Spec — task-monitoring (delta)

Capability: `task-monitoring`
Status: proposed
Source change: `004-monitoreo-tareas`

This spec defines the delta requirements for observability of asynchronous Huey tasks. It replaces
the legacy framing that assumed a `djhuey` migration; the current system uses a raw `SqliteHuey`
(`config/huey.py:7-10`). Requirements are anchored to the two existing task types:
`generate_invoice_pdf_and_email_task` (`apps/core/tasks.py:11`) and `send_email_task`
(`apps/core/tasks.py:34`).

## Requirement: TASK-LOG-1 — Lifecycle persistence

The system SHALL record each Huey task execution in a `TaskExecutionLog` model in the primary
database.

- The model SHALL have at least: `task_id`, `task_name`, `status`, `enqueued_at`, `started_at`,
  `finished_at`, `attempts`, `error_message`, `traceback`, `args_repr`.
- The model SHALL NOT use soft delete (auxiliary/transactional per project convention).
- `status` SHALL be one of: `ENQUEUED`, `EXECUTING`, `SUCCESS`, `ERROR`, `RETRYING`, `REVOKED`.

### Scenario: task enqueued

- **Given** a Huey task is enqueued
- **When** the `SIGNAL_ENQUEUED` signal fires
- **Then** a `TaskExecutionLog` row exists with `status = ENQUEUED` and `enqueued_at` set

### Scenario: task succeeds

- **Given** an existing `TaskExecutionLog` row for a task
- **When** the task finishes without error
- **Then** the row `status` becomes `SUCCESS` and `finished_at` is set

## Requirement: TASK-LOG-2 — Signal-driven capture

The system SHALL capture lifecycle transitions via Huey signal handlers registered in
`apps/core/apps.py` `ready()`.

- Signal handlers SHALL upsert the `TaskExecutionLog` row keyed by `task.id`.
- `SIGNAL_ERROR` and `SIGNAL_RETRYING` handlers SHALL store `error_message` and `traceback` and
  increment `attempts`.
- Signal handlers MUST NOT raise into the worker (failures MUST be contained and logged only).

### Scenario: task fails

- **Given** a task raises an exception during execution
- **When** the `SIGNAL_ERROR` signal fires with `exc`
- **Then** the matching `TaskExecutionLog` row has `status = ERROR`, `attempts >= 1`,
  `error_message` populated, and `traceback` non-empty

### Scenario: task retries

- **Given** a task is configured with `retries >= 1`
- **When** the `SIGNAL_RETRYING` signal fires
- **Then** the row `status` becomes `RETRYING` and `attempts` is incremented

## Requirement: TASK-RETRY-1 — Retry semantics & failure visibility

Both existing tasks SHALL be configured with retry behavior, and `send_email_task` SHALL NOT
swallow exceptions.

- `generate_invoice_pdf_and_email_task` and `send_email_task` SHOULD use `retries >= 1`,
  `retry_delay`, and `retry_backoff`.
- `send_email_task` MUST allow exceptions from `email.send()` to propagate (the `try/except`
  swallow at `apps/core/tasks.py:59-62` SHALL be removed).

### Scenario: email send failure is visible

- **Given** `send_email_task` is invoked and `email.send()` raises
- **When** the task executes
- **Then** the exception propagates, Huey emits `SIGNAL_ERROR`, and the task is retried per config
  (rather than being silently logged and marked successful)

## Requirement: TASK-VIEW-1 — Superuser monitoring view

The system SHALL provide a superuser-only Dashboard view (`dashboard:tasks`) listing task
executions with status, attempts, and tracebacks.

- The view SHALL require `is_superuser` (reuse the `DashboardView` guard pattern).
- The view SHALL show a visual alert (red banner) when any task has been `ENQUEUED` for more than
  5 minutes without starting (`status = ENQUEUED` and `enqueued_at < now - 5min`).
- The view SHALL show a warning for any `ERROR` execution with an expandable traceback.

### Scenario: stale queue alert

- **Given** a `TaskExecutionLog` row with `status = ENQUEUED` and `enqueued_at` older than 5 minutes
- **When** a superuser opens `dashboard:tasks`
- **Then** a red banner is displayed indicating at least one task is stale in the queue

### Scenario: non-superuser blocked

- **Given** a user who is not a superuser
- **When** they request `dashboard:tasks`
- **Then** access is denied (redirected to login / 403 per the project guard)

## Requirement: TASK-ADMIN-1 — Admin visibility

`TaskExecutionLog` SHALL be registered in Django admin as a read-only, filterable list
(`status` filter; columns `task_name`, `status`, `attempts`, `enqueued_at`, `finished_at`).

### Scenario: admin inspects failures

- **Given** failed task executions exist
- **When** a staff admin opens the `TaskExecutionLog` admin list filtered by `status = ERROR`
- **Then** the failing executions are listed with their attempts and timestamps
