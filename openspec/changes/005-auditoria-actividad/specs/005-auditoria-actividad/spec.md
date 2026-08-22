# Spec — Activity Audit Log (005-auditoria-actividad)

Delta requirements over the current `log_action` → `LogEntry` recording.

## Requirement: ACT-1 — Project-owned audit store

The system SHALL persist a project-owned `ActivityLog` record for every call to
`log_action` (`apps/core/utils.py:45`), in addition to the existing `LogEntry` write.

- **Given** any view handler invokes `log_action(user, obj, action_flag, message)`
- **When** the call returns
- **Then** exactly one `ActivityLog` row exists with the same `user`, `action_flag`,
  `content_type`, `object_id`, `object_repr`, and `message`.

The `ActivityLog` model SHALL NOT extend `SoftDeleteModel`; audit rows MUST remain
permanently visible to authorized users (compliance immutability).

## Requirement: ACT-2 — Request context capture

`log_action` SHOULD capture the actor's IP address and user-agent when a request is
available.

- **Given** `log_action(..., request=request)` (or `log_activity_from_request(request, ...)`)
  is called with `request.META['REMOTE_ADDR']` set
- **When** the audit row is created
- **Then** `ip_address` equals `REMOTE_ADDR` and `user_agent` equals
  `HTTP_USER_AGENT`.

- **Given** `log_action` is called without a request (existing ~30 call sites)
- **When** the audit row is created
- **Then** `ip_address` and `user_agent` are `NULL`/empty and the call still succeeds
  (backward compatibility is REQUIRED).

## Requirement: ACT-3 — Superuser aggregate view (admin)

The `ActivityLog` model SHALL be registered in `apps/core/admin.py` so superusers can
browse activity.

- **Given** a superuser is authenticated in the Django admin
- **When** they open the `ActivityLog` changelist
- **Then** rows are listed with `user`, `action_flag`, and `action_time` filters and
  search over `object_repr`, `message`, and `ip_address`.

## Requirement: ACT-4 — Superuser Tabler view (SHOULD)

The system SHOULD expose a Tabler list view at `core:activity_log`.

- **Given** a superuser requests the `auditoria/` URL
- **When** the page renders
- **Then** results are filtered by user, `action_flag`, and date range, paginated by 20.

- **Given** a non-superuser requests the same URL
- **When** access is evaluated
- **Then** the response is `403 Forbidden`.

## Requirement: ACT-5 — Permission & indexing conventions

`ActivityLog` MUST declare `default_permissions = ()` plus the four custom permissions
`view_activitylog`, `add_activitylog`, `change_activitylog`, `delete_activitylog`, and
MUST index `action_time`, `user`, and `action_flag` for query performance.

## Requirement: ACT-6 — Test coverage

The change MUST add `apps/core/tests/test_activity_log.py` (label `apps.core`) proving
ACT-1 through ACT-5, and `python manage.py test` MUST pass.
