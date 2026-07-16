# 021 · Eliminar campos planos de Forecasts

**Estado:** implementado

## Qué hace

Elimina los ~60 campos planos del modelo Forecasts que ya están normalizados en ForecastRegions y ForecastExtendedDay (Feature 013). Mantiene solo uuid, date, lp, nlp, nlpd, sunrise, sunset, uv_index.

## Criterios de aceptación

- [x] Migración elimina columnas planas
- [x] ForecastsForm actualizado (solo campos astronómicos + date)
- [x] Templates crear/actualizar actualizados
- [x] DashboardView charts leen de ForecastRegions
- [x] API serializer no referencia campos planos
- [x] `python manage.py test` — todos pasan
