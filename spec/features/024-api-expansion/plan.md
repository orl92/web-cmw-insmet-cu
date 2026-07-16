# 024 · API expansion — Plan

## Enfoque

Solo lectura (GET). Serializers simples. URLs bajo `/api/`. Usar drf-spectacular para documentación.

## Implementación

1. Serializers: EarlyWarningSerializer, TropicalCycloneSerializer, StormWarningSerializer, WeatherReportSerializer, ScientificPublicationSerializer, ServiceSerializer
2. Views: ListAPIView o RetrieveAPIView según corresponda
3. URL patterns en api/urls.py
4. Permisos: anon read, authenticated write (solo GET)
