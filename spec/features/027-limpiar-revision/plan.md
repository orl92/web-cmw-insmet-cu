# Plan · 027 · Limpieza de código (hallazgos de revisión)

## Archivos a modificar

| Archivo | Cambio |
|---|---|
| `.gitignore` | + `huey.db` |
| `dashboard/tests/test_views.py:7-18` | Remover `Invoice`, `Service`, `ServiceSubscription`, `StormWarning` del import |
| `api/tests/test_api.py` | 8 líneas `.filter(pk=1).update(...)` removidas |
| `dashboard/tests/test_views.py:30` | 1 línea `.filter(pk=1).update(...)` removida |
| `accounts/tests/test_views.py:23` | 1 línea `.filter(pk=1).update(...)` removida |

## Sin cambios funcionales

Todas las correcciones son de limpieza — ningún cambio en lógica de negocio, modelos, vistas o templates.
