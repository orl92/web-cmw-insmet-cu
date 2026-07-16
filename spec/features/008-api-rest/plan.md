# 008 · API REST — Plan

## Enfoque

DRF con 3 endpoints públicos de solo lectura. Serializers con datos anidados (ForecastSerializer produce JSON con 3 regiones + extendido + astronomía). Documentación con drf-spectacular sidecar. Decodificación de datos synop FM-12 desde archivos locales.

## Implementación

1. **Serializers**: `StationSerializer` (ModelSerializer), `StationObservationSerializer` (Serializer con field `data` JSON), `ForecastSerializer` (ModelSerializer con SerializerMethodField para JSON anidado de regiones, extendido y astronomía).
2. **Vistas**: `StationListAPIView` (ListAPIView), `StationObservationView` (GenericAPIView + GET → GetData().get_station()), `ForecastAPIView` (GenericAPIView + GET).
3. **Documentación**: `SpectacularSwaggerView`, `SpectacularRedocView`, `SpectacularAPIView` en api/urls.py.
4. **Config**: `REST_FRAMEWORK` en settings.py con `DEFAULT_THROTTLE_RATES` y `DEFAULT_PERMISSION_CLASSES = ['DjangoModelPermissionsOrAnonReadOnly']`.
5. **Decodificación**: Capa de datos en `api/data/` — GetData, OpenFileObs, Descodificador, FM12, Tablas, FileObs.

## Decisiones

- **drf-spectacular con sidecar** — evita CDN externo para Swagger UI; todo corre localmente.
- **Datos synop desde archivos locales** — las observaciones se almacenan en archivos FM-12 en el servidor; no hay BD de observaciones.
- **AllowAny en vistas** — override del default DjangoModelPermissionsOrAnonReadOnly porque no hay modelo BD detrás de observation, y stations/forecast son públicos.
- **Throttle por hora** — 100/h anónimo es suficiente para integración; 1000/h para usuarios registrados.

## Riesgos

- **Archivos FM-12 no disponibles** — si los archivos de observación no existen, el endpoint devuelve 404 o datos vacíos.
- **Formato synop cambia** — el decodificador está atado al formato FM-12 actual; cambios en el formato requerirían actualización.
