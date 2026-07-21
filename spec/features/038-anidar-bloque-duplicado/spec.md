# 038 — Anidar bloque duplicado en resumen_comercial.html

## Qué hace
El template `resumen_comercial.html` tiene dos bloques `{% if show_commercial and not is_client %}` separados (línea 3 y línea 168). El segundo bloque contiene el modal de detalle de suscripciones y debería anidarse dentro del primer bloque para eliminar la duplicación de la condición.

## Criterios de aceptación
- El modal de suscripciones está dentro del primer `{% if show_commercial and not is_client %}`
- No hay dos condiciones idénticas separadas
- Funcionalidad idéntica
