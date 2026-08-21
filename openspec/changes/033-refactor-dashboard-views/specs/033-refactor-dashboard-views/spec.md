# Spec — 033-refactor-dashboard-views

## Criterios de aceptación
- DashboardView → `dashboard/views/dashboard/dashboard.py`
- ExcelJSONView → `dashboard/views/dashboard/excel_json.py`
- MaintenanceModeToggleView → `dashboard/views/dashboard/maintenance.py`
- `_region_temp()` y `serialize_sub()` son funciones del módulo
- Subqueries `paid_direct`/`paid_via_items` definidas una sola vez
- `prefetch_related('user_set')` agregado en query de grupos
- `dashboard/urls.py` actualizado con nuevos imports
- `python manage.py test dashboard` pasa
