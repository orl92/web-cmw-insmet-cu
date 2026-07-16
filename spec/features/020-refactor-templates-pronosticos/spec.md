# 020 · Refactor templates de pronósticos

**Estado:** planificado

## Qué hace

Descompone los templates `crear_pronostico.html` (1,091 líneas) y `actualizar_pronostico.html` (1,093 líneas) en partials reutilizables. Actualmente son templates monolíticos sin ningún `{% include %}`.

## Criterios de aceptación

- [ ] Partial `region_fields.html` — parametrizado por prefijo (n/i/s) + booleano `has_mar`
- [ ] Partial `extended_day.html` — parametrizado por número de día (1-5)
- [ ] Partial `astro_fields.html` — datos astronómicos
- [ ] Crear y actualizar templates usan los partials
- [ ] Litepicker y forecast.js siguen funcionando
- [ ] `python manage.py test` — todos pasan
