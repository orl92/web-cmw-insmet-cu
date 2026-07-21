# Plan — 043-cleanup-dead-code

## Enfoque técnico
1. Verificar que WeatherToday, WeatherTomorrow, WeatherCommentary, WeatherNote no tienen referencias activas
2. Eliminar modelos viejos de dashboard/models.py (si no hay referencias)
3. Verificar que comentarios/ views no tienen URLs activas en dashboard/urls.py
4. Eliminar archivos de views de comentarios/nota_meteorologica y comentarios/tiempo
5. Eliminar templates asociadas a vistas viejas si existen
6. Reemplazar `print()` con `logger.debug()` o eliminar
7. Eliminar import `timedelta` no usado
8. Eliminar función JS duplicada

## App(s) modificadas
- dashboard/models.py
- dashboard/views/comentarios/
- dashboard/views/pronosticos/views.py
- dashboard/views/email_recipient/views.py
- static/dist/js/home-forecast.js
