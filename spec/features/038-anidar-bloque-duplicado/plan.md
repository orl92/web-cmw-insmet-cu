# Plan — 038-anidar-bloque-duplicado

## Enfoque técnico
1. Mover el bloque del modal (líneas 168-176 + `{% endif %}`) dentro del primer `{% if %}` (después de la línea 166)
2. Eliminar el segundo `{% if show_commercial and not is_client %}` y su `{% endif %}`
3. No hay cambios funcionales

## App(s) modificada(s)
- templates/includes/dashboard/resumen_comercial.html
