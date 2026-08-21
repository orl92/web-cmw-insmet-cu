# Spec — 049-homepage-refactor

## Criterios de aceptación

1. `<spam>` corregido a `<span>` en las líneas 212 y 216 del pronóstico extendido — se ve el layout correctamente.
2. Los 3 bloques de región climática (Costa Norte, Interior, Costa Sur) están extraídos a un partial `includes/home/forecast_region_card.html`.
3. El hack `class="invisible"` en Interior se reemplaza por `{% if m.sea %}` condicional.
4. Tooltips redundantes (que repiten el texto visible) se eliminan; solo se conservan tooltips que añadan información (ej: imágenes de clima).
5. SVG del índice UV se simplifica: se mantiene el mismo diseño visual del gauge circular, pero las 11 condiciones if/elif se reemplazan por cálculo matemático de la posición del indicador.
6. Imágenes below the fold usan `loading="lazy"`.
7. Los 3 SVGs de estado vacío ("No hay pronósticos disponibles", "No hay datos astronómicos", "No hay datos de índice UV") se extraen a `includes/home/empty_state.html`.
