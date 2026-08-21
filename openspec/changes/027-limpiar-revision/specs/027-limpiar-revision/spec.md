# Spec — 027-limpiar-revision

## Criterios de aceptación

- [x] `huey.db` agregado a `.gitignore`
- [x] Imports `Invoice`, `Service`, `ServiceSubscription`, `StormWarning` removidos de `dashboard/tests/test_views.py`
- [x] Llamadas `.filter(pk=1).update(maintenance_mode=False)` redundantes removidas (10 sitios en 3 archivos)
- [x] `python manage.py check` — sin errores
- [x] `python manage.py test` — 136 tests pasan
