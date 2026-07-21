# 032 — Refactor Dashboard Template: secciones a includes

## Qué hace
Divide `dashboard.html` (1667 líneas) en includes parciales por sección.
Unifica la paginación duplicada en un include reutilizable.

## Criterios de aceptación
- Las 5 secciones de dashboard.html son includes en `templates/includes/dashboard/`
- Paginación duplicada (líneas 165-192 y 260-289) en un solo `includes/pagination.html`
- `dashboard.html` conserva JS y CSS inline (contienen variables Django)
- El dashboard se ve y funciona exactamente igual
- `python manage.py test dashboard` pasa
