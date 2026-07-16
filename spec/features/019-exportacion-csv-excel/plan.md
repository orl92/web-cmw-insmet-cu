# 019 · Exportación CSV/Excel — Plan

## Enfoque

View genérica `CSVExportView` que recibe queryset + field list como kwargs. Usa `csv.writer` de Python (sin dependencias nuevas).

## Implementación

1. Crear `CSVExportView` mixin/view en common/views.py
2. URL `/dashboard/<modelo>/exportar/csv/` para cada modelo
3. Botón en templates de listado
4. Aplicar a Customer, Service, ServiceSubscription, Invoice, Forecasts, WeatherReport, EarlyWarning, TropicalCyclone, StormWarning
