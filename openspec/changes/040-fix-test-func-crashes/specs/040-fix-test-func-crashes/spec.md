# Spec — 040-fix-test-func-crashes

## Criterios de aceptación
- `ForecastUpdateView.test_func()` solo permite superusers (el modelo Forecasts no tiene owner)
- `EmailRecipientListUpdateView` usa `PermissionRequiredMixin` en vez de `UserPassesTestMixin` (si tiene permiso asignado) o solo superuser
- `GroupUpdateView.test_func()` solo permite superusers
- `python manage.py test` pasa
