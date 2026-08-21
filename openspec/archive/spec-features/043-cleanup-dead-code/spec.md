# 043 — Cleanup dead code

## Qué hace
Elimina código muerto identificado en la revisión:

1. **Viejos modelos de reportes**: WeatherToday, WeatherTomorrow, WeatherCommentary, WeatherNote (reemplazados por WeatherReport unificado)
2. **Viejas vistas de comentarios**: `dashboard/views/comentarios/tiempo/views.py`, `dashboard/views/comentarios/nota_meteorologica/views.py` (sin URLs activas)
3. **`print()` statements** en `dashboard/views/email_recipient/views.py` (4 lugares)
4. **Import no usado**: `timedelta` en `dashboard/views/pronosticos/views.py`
5. **Duplicado JS**: `getSeaConditionTitle()` definido 2 veces en `static/dist/js/home-forecast.js`

## Criterios de aceptación
- Código muerto eliminado (modelos, vistas, imports)
- `print()` reemplazados por `logger.debug()` o eliminados
- JS duplicado eliminado
- `python manage.py test` pasa
