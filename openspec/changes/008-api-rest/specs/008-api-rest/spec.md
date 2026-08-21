# Spec — 008-api-rest

## Criterios de aceptación

- [x] `GET /api/stations/` — lista todas las estaciones (número, nombre, provincia, coordenadas).
- [x] `GET /api/station/observation/<hour>/<station_number>/` — observación decodificada de una estación (temp, humedad, viento, precipitación, etc.).
- [x] `GET /api/forecast/<date>/` — pronóstico detallado con 3 regiones, extendido 5 días y astronomía, en JSON estructurado.
- [x] Documentación Swagger en `/api/doc/` y Redoc en `/api/redoc/`.
- [x] Schema OpenAPI en `/api/schema/`.
- [x] Rate limiting: anónimo 100/h, autenticado 1000/h.
- [x] Permisos: AllowAny en endpoints públicos (lectura global).
