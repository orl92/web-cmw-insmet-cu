# Spec — 032-refactor-dashboard-template

## Criterios de aceptación
- Las 5 secciones de dashboard.html son includes en `templates/includes/dashboard/`
- Paginación duplicada (líneas 165-192 y 260-289) en un solo `includes/pagination.html`
- `dashboard.html` conserva JS y CSS inline (contienen variables Django)
- El dashboard se ve y funciona exactamente igual
- `python manage.py test dashboard` pasa
