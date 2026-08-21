# 040 — Fix 3 test_func() crashes (campo user inexistente)

## Qué hace
Corrige 3 vistas cuyo `test_func()` referencia `self.get_object().user` en modelos que no tienen campo `user`.

### Vistas afectadas:
1. `ForecastUpdateView` — `dashboard/views/pronosticos/views.py:194`
2. `EmailRecipientListUpdateView` — `dashboard/views/email_recipient/views.py:131`
3. `GroupUpdateView` — `accounts/views/group/views.py:226`

## Criterios de aceptación
- `ForecastUpdateView.test_func()` solo permite superusers (el modelo Forecasts no tiene owner)
- `EmailRecipientListUpdateView` usa `PermissionRequiredMixin` en vez de `UserPassesTestMixin` (si tiene permiso asignado) o solo superuser
- `GroupUpdateView.test_func()` solo permite superusers
- `python manage.py test` pasa
