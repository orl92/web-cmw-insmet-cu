# Design — Activity Audit Log (005-auditoria-actividad)

## Current State (anchored to code)

| Concern | Reality |
|---|---|
| Recording primitive | `log_action(user, obj, action_flag, message)` at `apps/core/utils.py:45-53`, writing to `django.contrib.admin.models.LogEntry` via `LogEntry.objects.log_action(...)`. |
| Coverage | ~30 handlers already call it across `apps/commercial/` (`customers.py:64,104,139,159`, `invoices.py`, `subscriptions.py`, `contracts.py`, `services.py`, `certificates.py`), `apps/user_auth/` (`login.py:41,51`, `users.py`, `groups.py`, `profile.py`, `password.py`, `permission_profiles.py`), `apps/meteo/` (`province.py`, `town.py`, `station.py`, `forecast.py`, `warning.py`, `weather_report.py`), `apps/publications/views.py`, and `apps/core/` (`maintenance.py`, `company_settings.py`, `email_recipients.py`). |
| Action flags | `ADDITION=1, CHANGE=2, DELETION=3` from `django.contrib.admin.models`; custom `LOGIN_ACTION=4, LOGOUT_ACTION=5` at `apps/user_auth/views/login.py:10-11`. |
| IP / request context | Absent: `log_action` takes no `request`, so `REMOTE_ADDR` is never stored. |
| Aggregate view | None. No `admin.register(LogEntry)` exists; Django admin only offers per-object history. |
| Conventions available | `SoftDeleteModel` (`apps/core/models.py:53`), `FileHandlerMixin` (`:25`), custom-perm pattern `default_permissions=()` + 4 perms (`apps/commercial/models.py:72-78`), `core` urls `app_name='core'` (`apps/core/urls.py:1`), admin `@admin.register` style (`apps/core/admin.py:21-24`). |

## Decisions

### D1 — Own the audit store (`ActivityLog`), keep `LogEntry` writes
`LogEntry` is Django's table, not part of our domain; it cannot carry IP / user-agent
and has no project query surface. We introduce `ActivityLog` in `apps/core` as the
canonical, queryable audit store and **keep** the existing `LogEntry` writes for zero
regression. The `ActivityLog` row is created by the same `log_action` call (additive).

### D2 — Backward-compatible recording (no 99-call-site churn)
`log_action` keeps its signature `(user, obj, action_flag, message)` and gains an
optional `request=None`. Every current caller keeps working and now also populates
`ActivityLog` (IP blank until retrofitted). A convenience
`log_activity_from_request(request, obj, action_flag, message)` resolves
`request.user` and forwards the request. Retrofitting request-aware capture into the
auth and commercial mutating views is SHOULD-scope, not mandatory.

### D3 — Audit rows are immutable (deliberate soft-delete deviation)
AGENTS.md mandates `SoftDeleteModel` for business data with sensitive info. Audit rows
are **regulatory evidence** and MUST NOT be hidden via `record_active=False`. Therefore
`ActivityLog` does **not** extend `SoftDeleteModel`; deletion is prevented at the view
layer (superuser-only read; no delete view exposed) and the model exposes only the 4
custom perms without a public delete URL. This is a justified, documented exception.

### D4 — Viewing: admin first, Tabler view second
The admin registration (`apps/core/admin.py`) is the MUST delivery: superuser-gated for
free, with `list_filter=(user, action_flag, action_time)` and
`search_fields=(object_repr, message, ip_address)`. A Tabler `ActivityLogListView`
(`apps/core/views/activity_log.py`) with filters + `paginate_by=20` is SHOULD: audit
volume warrants server pagination (no DataTables), and non-superusers get `403`.

### D5 — Indexing for query performance
Add `db_index=True` on `action_time`, `user`, and `action_flag`, and a composite index
on `(action_flag, action_time)` to keep the filtered admin/list views fast as the table
grows.

## Data Model (delta)

`apps/core/models.py` — new class `ActivityLog(models.Model)`:

- `uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)`
- `user = models.ForeignKey(AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='activity_logs')`
- `action_flag = models.PositiveSmallIntegerField(choices=ACTIVITY_FLAG_CHOICES)` where
  `ACTIVITY_FLAG_CHOICES = ((1,'Adición'),(2,'Cambio'),(3,'Eliminación'),(4,'Inicio de sesión'),(5,'Cierre de sesión'))`
- `content_type = models.ForeignKey(ContentType, null=True, on_delete=models.SET_NULL)`
- `object_id = models.CharField(max_length=255, null=True)`
- `object_repr = models.TextField()`
- `message = models.TextField()`
- `ip_address = models.GenericIPAddressField(null=True)`
- `user_agent = models.TextField(null=True)`
- `action_time = models.DateTimeField(auto_now_add=True)`
- `class Meta: db_table='core_activity_log'; default_permissions=(); permissions=(('view_activitylog','Ver'),('add_activitylog','Añadir'),('change_activitylog','Editar'),('delete_activitylog','Eliminar')); indexes=[...]`

## Recording Change (delta)

`apps/core/utils.py:45` — `log_action` body extended:

```python
def log_action(user, obj, action_flag, message, request=None):
    LogEntry.objects.log_action(
        user_id=user.pk,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=str(obj),
        action_flag=action_flag,
        change_message=message,
    )
    ActivityLog.objects.create(
        user=user if isinstance(user, User) else None,
        action_flag=action_flag,
        content_type=ContentType.objects.get_for_model(obj),
        object_id=str(obj.pk),
        object_repr=str(obj),
        message=message,
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
    )
```

`log_activity_from_request(request, obj, action_flag, message)` delegates to
`log_action(request.user, obj, action_flag, message, request=request)`.

## Viewing Change (delta)

- `apps/core/admin.py`: `@admin.register(ActivityLog)` →
  `list_display=('action_time','user','action_flag','object_repr')`,
  `list_filter=('user','action_flag','action_time')`,
  `search_fields=('object_repr','message','ip_address')`.
- `apps/core/views/activity_log.py` (SHOULD): `ActivityLogListView` (superuser-only,
  `403` otherwise) with `FilterSet`-style filters (user / action_flag / date range) and
  `paginate_by = 20`. URL `auditoria/` name `activity_log` in `apps/core/urls.py`.

## Migration

`python manage.py makemigrations core` creates one table. Migrations are NOT versioned
(`.gitignore`). No data migration of business rows.

## Tests

`apps/core/tests/test_activity_log.py` (label `apps.core`):

1. Calling `log_action(...)` creates exactly one `ActivityLog` and one `LogEntry`.
2. `log_activity_from_request` stores `ip_address` from `request.META`.
3. Admin registration exists and exposes the configured `list_filter`.
4. `ActivityLogListView` returns `200` for a superuser and `403` for a non-superuser;
   date/user/action filters narrow the queryset.

## Verification

- `python manage.py check`
- `python manage.py test apps.core`
- `python manage.py test` (full suite, per CI push-to-main)
- `python manage.py makemigrations --check` stays green.
