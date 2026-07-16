# 020 · Refactor templates de pronósticos — Plan

## Enfoque

Extraer partials manteniendo el mismo markup HTML, IDs de campo, y clases CSS para no romper JavaScript (Litepicker, forecast.js).

## Implementación

1. Crear `includes/dashboard/pronosticos/region_fields.html` con parámetros `prefix`, `title`, `has_mar`
2. Crear `includes/dashboard/pronosticos/extended_day.html` con parámetro `day_number`
3. Crear `includes/dashboard/pronosticos/astro_fields.html`
4. Refactorizar `crear_pronostico.html` (incluir partials)
5. Refactorizar `actualizar_pronostico.html`
6. Opcional: unificar crear/actualizar con `{% if form.instance.pk %}`
