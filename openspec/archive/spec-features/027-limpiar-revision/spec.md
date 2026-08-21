# 027 · Limpieza de código (hallazgos de revisión)

**Estado:** completado

## Qué hace

Corrige 3 hallazgos de la revisión de código: `huey.db` sin gitignore, imports no usados, y llamadas a `.update()` redundantes en tests.

## Criterios de aceptación

- [x] `huey.db` agregado a `.gitignore`
- [x] Imports `Invoice`, `Service`, `ServiceSubscription`, `StormWarning` removidos de `dashboard/tests/test_views.py`
- [x] Llamadas `.filter(pk=1).update(maintenance_mode=False)` redundantes removidas (10 sitios en 3 archivos)
- [x] `python manage.py check` — sin errores
- [x] `python manage.py test` — 136 tests pasan
