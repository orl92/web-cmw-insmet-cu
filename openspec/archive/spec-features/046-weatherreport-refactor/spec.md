# 046 — WeatherReport refactor (type field, triple save)

## Qué hace
Corrige issues en WeatherReport:

1. **`dashboard/models.py:727`** — Campo `type` sombrea built-in de Python. Renombrar a `report_type`
2. **`dashboard/views/tiempo/views.py:251-263`** — `form_valid()` guarda el objeto 3 veces (commit=False + save() + super().form_valid())

## Criterios de aceptación
- `type` renombrado a `report_type` en modelo, forms, vistas, templates, API
- `form_valid()` guarda una sola vez
- `python manage.py test` pasa
