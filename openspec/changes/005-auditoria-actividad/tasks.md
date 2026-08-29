# Tasks — 005-auditoria-actividad

## Phase 1 — Model & Migration

- [x] Add `ActivityLog` model to `apps/core/models.py` (uuid, user FK null, action_flag
       + choices ADDITION/CHANGE/DELETION/LOGIN/LOGOUT, content_type, object_id,
       object_repr, message, ip_address, user_agent, action_time; `default_permissions=()`
       + 4 custom perms; indexed; NOT soft-deleted).
- [x] Run `python manage.py makemigrations core` and verify the migration is created
       (not versioned per `.gitignore`).

## Phase 2 — Recording Extension

- [x] Extend `log_action` (`apps/core/utils.py:45`) to also create `ActivityLog`, adding
       an optional `request=None` param (backward compatible — all ~30 existing call
       sites keep working).
- [x] Add `log_activity_from_request(request, obj, action_flag, message)` convenience
       helper in `apps/core/utils.py`.
- [x] (SHOULD) Retrofit request-aware logging into `apps/user_auth/views/login.py`
       (login/logout) and selected `apps/commercial/views/*` mutating handlers so IP is
       captured for the highest-value events.

## Phase 3 — Viewing Layer

- [x] Register `ActivityLog` in `apps/core/admin.py` with `list_display`,
       `list_filter=(user, action_flag, action_time)`, `search_fields`.
- [x] (SHOULD) Add `ActivityLogListView` in `apps/core/views/activity_log.py`
       (superuser-only, `403` otherwise) with filters + `paginate_by=20`, and wire URL
       `auditoria/` name `activity_log` into `apps/core/urls.py` (`app_name='core'`).

## Phase 4 — Tests & Verification

- [x] Add `apps/core/tests/test_activity_log.py` covering recording, IP capture, admin
       registration, and superuser/non-superuser view behavior.
- [x] Run `python manage.py check && python manage.py test apps.core`.
- [x] Run full suite `python manage.py test` (CI parity) and confirm
       `makemigrations --check` is green.
