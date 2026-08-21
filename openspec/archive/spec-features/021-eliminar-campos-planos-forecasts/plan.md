# 021 · Eliminar campos planos de Forecasts — Plan

## Enfoque

Migración que dropea columnas. Actualizar form, vistas, templates, API. Peligro: perder datos si hay registros no migrados (ejecutar migrate_forecast_data primero).

## Implementación

1. Marcar campos planos como `editable=False` o eliminarlos del modelo
2. Migración
3. Actualizar ForecastsForm (solo date + astronómicos)
4. Actualizar AllForecastCreateView y ForecastUpdateView
5. Actualizar templates (dejan de referenciar campos planos)
6. Actualizar DashboardView (chart data desde ForecastRegions)
7. Verificar API serializer
