# Proposal

## Intent

Provide a queryable, project-owned **user activity audit trail** for security and
compliance. Today the system already records most mutating actions, but the trail is
scattered and incomplete for auditing purposes:

- The recording primitive `log_action(user, obj, action_flag, message)` exists at
  `apps/core/utils.py:45` and already persists to `django.contrib.admin.models.LogEntry`.
  It is already invoked from ~30 view handlers across `apps/commercial/`,
  `apps/user_auth/`, `apps/meteo/`, `apps/publications/`, and `apps/core/`
  (e.g. `apps/commercial/views/customers.py:64,104,139,159`,
  `apps/user_auth/views/login.py:41,51`).
- `LogEntry` is Django's table: it is not part of our domain, cannot capture the
  request IP / user-agent, and has **no admin changelist registered** anywhere
  (verified: no `admin.register(LogEntry)` in the codebase), so there is no
  superuser-facing, filterable, aggregate view of activity.
- `log_action` has no `request` parameter, so the actor's IP is never recorded
  (`apps/core/utils.py:45-53`).

This change makes the audit trail first-class and observable without rewriting the
existing ~30 call sites.

## Scope In

- **`ActivityLog` model** in `apps/core/models.py` — a project-owned, immutable audit
  store carrying `user`, `action_flag`, `content_type`, `object_id`, `object_repr`,
  `message`, `ip_address`, `user_agent`, and `action_time`.
- **Recording extension** — `log_action` (backward compatible) also writes an
  `ActivityLog` row on every existing call site, plus a request-aware helper that
  captures IP / user-agent.
- **Superuser viewing layer** — register `ActivityLog` in `apps/core/admin.py` with
  filters and search (satisfies "admin views"); add a Tabler superuser list view with
  filters and pagination (satisfies "log view for superusers").
- **Tests** under `apps/core/tests/` (label `apps.core`) proving the recording and
  viewing behavior.

## Scope Out

- Custom Django `Middleware` that logs every request. The current event-based
  `log_action` approach is already the established pattern; a blanket request logger
  is explicitly excluded to avoid noisy, low-value rows and performance cost.
- Encrypting or exporting audit data to external systems (SIEM, cold storage).
- Retrofitting IP capture into **all** ~30 existing call sites — only the
  highest-value views (auth + commercial mutations) are in scope; the rest populate
  `ActivityLog` without IP until retrofitted.
- Changing the existing `LogEntry` writes (kept for zero regression).

## Approach

1. **Model — `apps/core/models.py`** (new `ActivityLog`, after `SoftDeleteModel` at
   `:53`):
   - `uuid = UUIDField(default=uuid.uuid4, editable=False, unique=True)` (exposed PK
     per convention).
   - `user = ForeignKey(AUTH_USER_MODEL, null=True, on_delete=SET_NULL)` — nullable so
     system/anon events still record.
   - `action_flag = PositiveSmallIntegerField(choices=...)` with choices
     `ADDITION=1, CHANGE=2, DELETION=3, LOGIN=4, LOGOUT=5` (the custom `4/5` already
     used at `apps/user_auth/views/login.py:10-11`).
   - `content_type = ForeignKey(ContentType, null=True)`, `object_id = CharField(null=True)`,
     `object_repr = TextField()`, `message = TextField()`.
   - `ip_address = GenericIPAddressField(null=True)`, `user_agent = TextField(null=True)`.
   - `action_time = DateTimeField(auto_now_add=True)`.
   - `class Meta: default_permissions = ()` + 4 custom perms
     `view_/add_/change_/delete_activitylog` (pattern at
     `apps/commercial/models.py:72-78`). **Not** `SoftDeleteModel`: audit rows must be
     permanent for compliance (deliberate deviation, see design.md).
   - `index_together`/`db_index` on `action_time`, `user`, `action_flag` for query speed.

2. **Recording — `apps/core/utils.py:45`**: extend `log_action` to also create
   `ActivityLog` in the same call. Add an optional `request=None` parameter
   (backward compatible — all 99 existing calls keep working) that, when present,
   populates `ip_address` (`request.META.get('REMOTE_ADDR')`) and `user_agent`.
   Add a thin `log_activity_from_request(request, obj, action_flag, message)` that
   resolves `request.user` and forwards the request. Retrofit the request-aware helper
   into `apps/user_auth/views/login.py` and selected `apps/commercial/views/*`
   mutating handlers (SHOULD).

3. **Viewing — `apps/core/admin.py`** (register style at `apps/core/admin.py:21-24`):
   `@admin.register(ActivityLog)` with `list_display`
   (`action_time, user, action_flag, object_repr`), `list_filter`
   (`user, action_flag, action_time`), `search_fields`
   (`object_repr, message, ip_address`). Admin is superuser-gated by Django.

4. **Viewing (SHOULD) — `apps/core/views/activity_log.py`**: `ActivityLogListView`
   (superuser only; `403` otherwise) with filters (user, action_flag, date range) and
   `paginate_by = 20` (no DataTables — audit volume warrants server pagination, per
   AGENTS.md convention). URL `auditoria/` name `activity_log` added to
   `apps/core/urls.py` (`app_name='core'`, `:1`).

5. **Migration**: `python manage.py makemigrations core` — new table only; NOT
   versioned (`.gitignore` per convention).

6. **Tests**: `apps/core/tests/test_activity_log.py` (label `apps.core`) verifying
   `log_action` creates an `ActivityLog`, the request-aware helper captures IP, the
   admin registration exists, and the superuser view filters while non-superusers get
   `403`.

## Acceptance Criteria

- [ ] `ActivityLog` exists in `apps/core/models.py` with `uuid`, `user`, `action_flag`
      (+ choices incl. LOGIN=4/LOGOUT=5), `content_type`, `object_id`, `object_repr`,
      `message`, `ip_address`, `user_agent`, `action_time`; `default_permissions = ()`
      + 4 custom perms; NOT soft-deleted.
- [ ] `log_action` (`apps/core/utils.py:45`) persists an `ActivityLog` row on every
      existing call site with **no signature break** (backward compatible).
- [ ] When a `request` is supplied, `ip_address` and `user_agent` are captured
      (`log_activity_from_request` or `request=` param).
- [ ] `ActivityLog` is registered in `apps/core/admin.py` with
      `list_filter=(user, action_flag, action_time)` and `search_fields`.
- [ ] (SHOULD) Superuser Tabler list view with filters + `paginate_by=20`; non-superuser
      receives `403`.
- [ ] `python manage.py makemigrations core` runs cleanly; `python manage.py test`
      (full suite) passes.
- [ ] `apps/core/tests/test_activity_log.py` exists and passes with label `apps.core`.

## Rollback

The change is strictly additive:

- New DB table (`ActivityLog`) and a new admin registration; `log_action` extension is
  additive and `LogEntry` writes are preserved, so removing the `ActivityLog` write is
  low-risk.
- Rollback steps: `python manage.py migrate core zero` to drop the table, then revert
  the model / `log_action` / admin / view edits. No business data is migrated.
- `python manage.py makemigrations --check` must stay green after revert.
