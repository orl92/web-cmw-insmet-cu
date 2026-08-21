# 014 · Refactor reportes meteorológicos

**Estado:** implementado

## Qué hace

Reduce la duplicación masiva entre los 4 modelos de reportes meteorológicos (`WeatherToday`, `WeatherTomorrow`, `WeatherCommentary`, `WeatherNote`) y sus respectivos formularios, vistas y URLs.

Actualmente cada modelo repite exactamente los mismos campos (uuid, user, date, summary, file, email_recipient_list) y cada uno tiene su propio form, 6 vistas (list/create/update/delete/detail/PDF) y 6 URLs. En total: ~400 líneas de vistas y ~60 líneas de formularios completamente duplicadas.

## Por qué

- 4 modelos con campos idénticos → cualquier cambio de campo requiere tocar 4 definiciones
- 4 forms casi idénticos (única diferencia: WeatherToday usa TextField vs CharField en summary)
- 24 clases de vista con 95% de código duplicado
- Añadir un nuevo tipo de reporte requiere copiar 4 archivos
- Las templates ya están parcialmente compartidas (form_crear.html / form_actualizar.html), pero el resto no

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

## Fuera de alcance

- Refactor de las templates de creación/edición (siguen siendo individuales por ahora)
- Cambios en el sistema de alertas (EarlyWarning, TropicalCyclone, StormWarning) — se queda como está
- Eliminación de los modelos viejos (se mantienen como respaldo hasta próxima iteración o se eliminan en esta si no hay datos)
