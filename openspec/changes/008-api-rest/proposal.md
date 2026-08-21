# 008 · API REST

**Estado:** implementado ✅

## Qué hace

API REST pública con 3 endpoints: listado de estaciones meteorológicas, observación de una estación en hora específica (decodifica datos FM-12 synop desde archivos locales), y pronóstico detallado por fecha. Documentación interactiva con Swagger UI y Redoc generada por drf-spectacular. Rate limiting: 100 req/hora para anónimos, 1000 para autenticados.

## Por qué

Integración con terceros (universidades, otras instituciones, apps). La API expone los datos del centro de forma estándar y documentada sin necesidad de acceso al dashboard.

## Criterios de aceptación

- [x] `GET /api/stations/` — lista todas las estaciones (número, nombre, provincia, coordenadas).
- [x] `GET /api/station/observation/<hour>/<station_number>/` — observación decodificada de una estación (temp, humedad, viento, precipitación, etc.).
- [x] `GET /api/forecast/<date>/` — pronóstico detallado con 3 regiones, extendido 5 días y astronomía, en JSON estructurado.
- [x] Documentación Swagger en `/api/doc/` y Redoc en `/api/redoc/`.
- [x] Schema OpenAPI en `/api/schema/`.
- [x] Rate limiting: anónimo 100/h, autenticado 1000/h.
- [x] Permisos: AllowAny en endpoints públicos (lectura global).

## Fuera de alcance

- Endpoints autenticados para escritura (POST/PUT/DELETE).
- Webhooks o notificaciones push.
- API versionada (solo v1 implícita).
