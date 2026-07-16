# 013 · Normalizar modelo Forecasts — Tareas

### Modelos

- [x] Crear `ForecastRegions` en dashboard/models.py
- [x] Crear `ForecastExtendedDay` en dashboard/models.py
- [x] Agregar properties bridge a Forecasts (`get_region_data`, `get_extended_days`)
- [x] Crear y ejecutar migración

### Migración de datos

- [x] Crear management command `migrate_forecast_data`
- [x] Copiar datos de campos planos a ForecastRegions (9 rows por forecast)
- [x] Copiar datos de campos planos a ForecastExtendedDay (5 rows por forecast)

### API

- [x] Actualizar `ForecastSerializer` para usar `ForecastRegions` y `ForecastExtendedDay`
- [x] Verificar que la salida JSON es idéntica (retrocompatible)
- [x] Ejecutar tests de API

### Home

- [x] Actualizar `IndexView` para precargar regiones y extended days
- [ ] Template index.html usa bridge properties (difiere a Feature 020 — refactor templates pronósticos)

### Dashboard

- [x] Actualizar `DashboardView` para usar nuevos modelos en charts
- [x] Actualizar `ForecastsListView` QuerySet con prefetch_related
- [ ] Templates de listado usan bridge properties (difiere a Feature 020 — refactor templates pronósticos)

### Templatetags

- [x] Actualizar `get_forecast_day` para soportar nuevos modelos

### Tests

- [x] Actualizar `dashboard/tests/test_models.py` — tests para ForecastRegions, ForecastExtendedDay
- [x] Actualizar `api/tests/test_api.py` — verificar JSON output
- [x] Ejecutar todos los tests

### Limpieza

- [x] `python manage.py check` — sin errores
- [x] `python manage.py test` — todos pasan
- [x] Actualizar roadmap.md
