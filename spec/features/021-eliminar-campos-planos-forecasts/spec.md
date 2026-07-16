# 021 · Eliminar campos planos de Forecasts

**Estado:** planificado

## Qué hace

Elimina los ~60 campos planos del modelo Forecasts que ya están normalizados en ForecastRegions y ForecastExtendedDay (Feature 013). Mantiene solo uuid, date, lp, nlp, nlpd, sunrise, sunset, uv_index.

## Criterios de aceptación

- [ ] Migración elimina columnas planas
- [ ] ForecastsForm actualizado (solo campos astronómicos + date)
- [ ] Templates crear/actualizar actualizados
- [ ] DashboardView charts leen de ForecastRegions
- [ ] API serializer no referencia campos planos
- [ ] `python manage.py test` — todos pasan
