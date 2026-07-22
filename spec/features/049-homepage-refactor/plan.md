# Plan — Feature 049

## Enfoque técnico

- Solo se modifica `templates/pages/home/index.html` y se crean partials en `templates/includes/home/`.
- No hay cambios de modelo, vista, URL ni base de datos.
- No requiere migraciones.

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `templates/pages/home/index.html` | Todos los ítems del spec |
| `templates/includes/home/forecast_region_card.html` | Nuevo: partial para una región climática |
| `templates/includes/home/empty_state.html` | Nuevo: partial para "sin datos" |

## Detalle de cambios

1. **`<spam>` → `<span>`**: Líneas 212 y 216.
2. **Extraer región climática**: El bloque de cada región (`.col-lg-4.mb-3 > .card`) se mueve a `forecast_region_card.html`. Se invoca 3 veces con `{% include %}` pasando la región como contexto.
3. **`invisible` → condicional**: En Interior, `{% if m.sea %}` decide si mostrar la línea de mar.
4. **Tooltips redundantes**: Los tooltips como `title="Temperatura: {{ m.temp }}°C"` sobre `{{ m.temp }}°C` se eliminan. Se conservan tooltips en imágenes de clima y en el índice UV.
5. **Índice UV**: Calcular la posición XY del círculo indicador usando una fórmula basada en el valor numérico del UV, en vez de 11 condiciones if/elif. El SVG de arcos se conserva sin cambios.
6. **`loading="lazy"`**: Agregar a imágenes de pronóstico extendido, fase lunar, salida/puesta de sol.
7. **Empty states**: Los 3 SVGs de "sin datos" se mueven a `empty_state.html` con un parámetro para el icono SVG a mostrar.
