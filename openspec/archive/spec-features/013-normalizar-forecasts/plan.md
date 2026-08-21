# 013 · Normalizar modelo Forecasts — Plan

## Enfoque

Crear modelos relacionados manteniendo el modelo original `Forecasts` como contenedor de astronómicos. Los datos regionales y extendidos se almacenan en modelos separados con `unique_together`. El serializador y las vistas se actualizan para leer desde los nuevos modelos. Los templates se refactorizan progresivamente.

## Implementación

1. **Nuevos modelos** en `dashboard/models.py`:
   - `ForecastRegions(FileHandlerMixin, models.Model)` — FK a Forecasts, region (north/interior/south), period (morning/afternoon/night), temp, weather, wind_dir, wind_speed, sea_note
   - `ForecastExtendedDay(models.Model)` — FK a Forecasts, day_number (1-5), date, min_temp, max_temp, weather

2. **Métodos bridge** en `Forecasts`:
   - `get_region_data(region)` — retorna los 3 períodos de una región
   - `get_extended_days()` — retorna los 5 días
   - `regions` property — dict con north/interior/south
   - `extended_forecast` property — lista de días

3. **Migración de datos**: management command o data migration que copia campos planos → modelos relacionados

4. **API**: actualizar `ForecastSerializer` para usar `ForecastRegions` y `ForecastExtendedDay` manteniendo misma estructura JSON de salida

5. **Home IndexView**: actualizar contexto para usar nuevas propiedades bridge

6. **Dashboard DashboardView**: actualizar chart data para usar nuevas propiedades

7. **Dashboard CRUD**: mantener formulario actual (sigue escribiendo en campos planos), pero leer desde modelos relacionados

8. **Templates**: refactor progresivo — primero solo lectura, escritura en siguiente iteración

9. **Templatetags**: actualizar `get_forecast_day` para funcionar con nuevos modelos

## Decisiones

- **No eliminar campos viejos aún** — los datos se migran a los nuevos modelos pero los campos planos se mantienen como respaldo (drop en feature futura)
- **Bridge properties** — permiten que templates y vistas existentes sigan funcionando sin cambios inmediatos
- **Incrementa filas pero reduce complejidad** — pasamos de 70 columnas a ForecastRegions (9 rows × 1 forecast) + ForecastExtendedDay (5 rows × 1 forecast)

## Riesgos

- **Rendimiento**: más queries (JOINs) para reconstruir datos. Mitigar con `select_related` y `prefetch_related`
- **Retrocompatibilidad**: la API debe devolver exactamente la misma estructura JSON
- **Campos de mar (sea_note)**: solo north y sur tienen mar. Interior tiene campos de mar seteados a None
