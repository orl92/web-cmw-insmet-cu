# Spec — 020-refactor-templates-pronosticos

## Criterios de aceptación

- [ ] Partial `region_fields.html` — parametrizado por prefijo (n/i/s) + booleano `has_mar`
- [ ] Partial `extended_day.html` — parametrizado por número de día (1-5)
- [ ] Partial `astro_fields.html` — datos astronómicos
- [ ] Crear y actualizar templates usan los partials
- [ ] Litepicker y forecast.js siguen funcionando
- [ ] Reordenar dashboard template — Gráficos Comerciales inmediatamente después de Resumen Comercial (agrupar widgets por tipo)
- [ ] `python manage.py test` — todos pasan
