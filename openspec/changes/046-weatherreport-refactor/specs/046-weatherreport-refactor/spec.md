# Spec — 046-weatherreport-refactor

## Criterios de aceptación
- `type` renombrado a `report_type` en modelo, forms, vistas, templates, API
- `form_valid()` guarda una sola vez
- `python manage.py test` pasa
