# 070 — tests-secundarios

## Plan

Cubrir las áreas con cobertura insuficiente o nula señaladas en el spec:
`DashboardView`, los middleware de `apps/core/` y las tareas Huey genéricas.

### Contexto

- `apps/dashboard/` no tiene carpeta `tests/`.
- `apps/core/tests/` solo tiene `test_email_recipient_views.py` y `test_file_handling.py`.
- `apps/core/tasks.py` define `generate_invoice_pdf_and_email_task` y `send_email_task` (Huey). No hay tests.
- `apps/core/middleware.py` define `CheckUserProfileMiddleware` y `MaintenanceModeMiddleware`. No hay tests.

### Enfoque

- Los tests usan el patrón de los existentes: `_disable_maintenance_mode()` /
  `SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})`
  en `setUpTestData` para que el modo mantenimiento no interfiera.
- Usuarios superuser con `first_name`/`last_name`/`email` completos para pasar
  `CheckUserProfileMiddleware` en las vistas (dashboard).
- Para `DashboardView`, usuarios cliente con `commercial_customer` con todos los
  campos requeridos llenos (account/agency_bank/address/phone; + company_name/
  reeup/nit si es jurídica).
- Las tareas Huey se invocan directamente (son funciones decoradas); el email se
  captura con `override_settings(EMAIL_BACKEND='...locmem...')` → `mail.outbox`.

### Archivos

| Archivo | Contenido |
|---|---|
| `apps/dashboard/tests/test_views.py` | `DashboardView`: acceso (anon/403/staff/cliente), context flags, rangos, KPIs/charts con datos |
| `apps/core/tests/test_middleware.py` | `CheckUserProfileMiddleware` + `MaintenanceModeMiddleware` |
| `apps/core/tests/test_tasks.py` | `send_email_task` con adjuntos (por args y por path) |

### Criterios de aceptación del spec → tests

1. DashboardView testea context con KPIs/charts/filter por grupo staff → `test_views.py`
2. Maintenance mode bloquea no-superusers excepto `/login/` → `test_middleware.py`
3. CheckUserProfileMiddleware redirige a completar perfil → `test_middleware.py`
4. send_email_task envía correo con adjuntos → `test_tasks.py`
5. `python manage.py test` pasa → verificación final

### Verificación

- `python manage.py check`
- `python manage.py test apps.dashboard apps.core`
- `python manage.py test` (suite completa)
