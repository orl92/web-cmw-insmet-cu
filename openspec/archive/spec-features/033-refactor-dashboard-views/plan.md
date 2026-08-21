# Plan — 033-refactor-dashboard-views

## Enfoque técnico
1. Crear `dashboard/views/dashboard/dashboard.py` con DashboardView
2. Crear `dashboard/views/dashboard/excel_json.py` con ExcelJSONView
3. Crear `dashboard/views/dashboard/maintenance.py` con MaintenanceModeToggleView
4. En dashboard.py: extraer _region_temp() y serialize_sub() como funciones del módulo
5. Extraer paid_direct/paid_via_items a nivel de módulo (reutilizadas en 2 queries)
6. Agregar `.prefetch_related('user_set')` a Group.objects.annotate(...) en DashboardView
7. Mover import pandas a excel_json.py (único usuario)
8. Actualizar dashboard/urls.py (cambiar imports)

## App(s) modificada(s)
- dashboard/views/dashboard/
- dashboard/urls.py

## Archivos nuevos
- dashboard/views/dashboard/dashboard.py
- dashboard/views/dashboard/excel_json.py
- dashboard/views/dashboard/maintenance.py
