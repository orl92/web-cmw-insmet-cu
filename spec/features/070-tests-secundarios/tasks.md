# 070 — tests-secundarios

## Tasks

### T1 · DashboardView tests
- [x] Crear `apps/dashboard/tests/test_views.py`
- [x] `test_anonymous_redirects_to_login`
- [x] `test_non_staff_non_client_forbidden` (403)
- [x] `test_staff_can_access_and_context_flags` (200; `selected_range='7d'`; `show_alerts`/`show_forecast` según permisos)
- [x] `test_range_query_param` (`30d`, `3m`, default)
- [x] `test_client_group_context` (is_client + subs/invoices vacíos o con datos)
- [x] `test_show_commercial_and_income_data` (staff con permisos commercial; `income_*` JSON parseable)
- [x] `test_forecast_chart_data` (con Forecasts + ForecastRegions; `temperature_labels`/`max_temperatures_*` JSON)

### T2 · Middleware tests
- [x] Crear `apps/core/tests/test_middleware.py`
- [x] `CheckUserProfileMiddleware`:
  - [ ] usuario sin email/nombre/apellido → redirect `/accounts/profile/update/`
  - [ ] usuario completo → 200
  - [ ] cliente natural con campos faltantes → redirect; completo → 200
  - [ ] cliente jurídica sin company_name/reeup/nit → redirect
  - [ ] no-redirect si path ya es el de update de perfil
- [x] `MaintenanceModeMiddleware`:
  - [ ] mantenimiento ON + no-superuser → redirect login
  - [ ] mantenimiento ON + superuser → 200
  - [ ] mantenimiento ON + `/login/` exento
  - [ ] mantenimiento OFF → 200

### T3 · Huey task tests
- [x] Crear `apps/core/tests/test_tasks.py`
- [x] `send_email_task` con `locmem` backend → 1 correo en `mail.outbox`, `content_subtype='html'`
- [x] con `attachment_name/content/mime` → adjunto presente
- [x] con `attachment_path` → adjunto presente (lee el archivo, mime pdf)
- [x] sin adjuntos → sin attachments

### T4 · Verificación
- [x] `python manage.py check`
- [x] `python manage.py test apps.dashboard apps.core`
- [x] `python manage.py test` (suite completa)
- [x] Actualizar `spec/constitution/roadmap.md` (070 → Hecho)
