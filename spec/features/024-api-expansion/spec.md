# 024 · API expansion

**Estado:** planificado

## Qué hace

Expande la API REST con endpoints para avisos, weather reports, publicaciones y servicios. Actualmente solo existen endpoints para Station, StationObservation y Forecast.

## Criterios de aceptación

- [x] GET `/api/early-warnings/` — retorna alertas activas
- [x] GET `/api/tropical-cyclones/` — retorna ciclones activos
- [x] GET `/api/storm-warnings/` — retorna tormentas activas
- [x] GET `/api/weather-reports/<type>/` — retorna weather report por tipo
- [x] GET `/api/publications/` — retorna publicaciones
- [x] GET `/api/services/` — retorna servicios públicos
- [x] Permisos: AllowAny (lectura pública)
- [x] Documentado en drf-spectacular (Swagger/ReDoc)
- [x] `python manage.py test` — todos pasan (133/133)
