# Spec — 014-refactor-reportes-tiempo

## Criterios de aceptación

- [ ] Los 4 modelos se refactorizan a un modelo único con campo `type` + 4 proxy models para permisos y verbose_names
- [ ] Migración de datos: registros existentes se migran a la tabla unificada sin pérdida
- [ ] Forms: un solo `WeatherReportForm` parametrizable por tipo
- [ ] Vistas: un solo set de vistas CRUD + PDF, parametrizadas por tipo de reporte
- [ ] Templates dashboard: se consolidan (una sola copia de listado/detalle/form por grupo)
- [ ] Templates públicas (home): se consolidan
- [ ] URLs: se mantienen los mismos nombres (backward compat) pero apuntan a vistas genéricas
- [ ] Permisos: se mantienen separados por tipo (view/add/change/delete_weather_today, etc.)
- [ ] `python manage.py test` — todos los tests pasan
- [ ] `python manage.py check` — sin errores
