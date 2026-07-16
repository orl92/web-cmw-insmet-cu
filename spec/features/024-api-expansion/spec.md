# 024 · API expansion

**Estado:** planificado

## Qué hace

Expande la API REST con endpoints para avisos, weather reports, publicaciones y servicios. Actualmente solo existen endpoints para Station, StationObservation y Forecast.

## Criterios de aceptación

- [ ] GET `/api/early-warnings/` — retorna alertas activas
- [ ] GET `/api/tropical-cyclones/` — retorna ciclones activos
- [ ] GET `/api/storm-warnings/` — retorna tormentas activas
- [ ] GET `/api/weather-reports/<type>/` — retorna weather report por tipo
- [ ] GET `/api/publications/` — retorna publicaciones
- [ ] GET `/api/services/` — retorna servicios públicos
- [ ] Permisos: DjangoModelPermissionsOrAnonReadOnly
- [ ] Documentado en drf-spectacular (Swagger/ReDoc)
- [ ] `python manage.py test` — todos pasan
