# Feature 053 — Eliminar duplicación responsive en servicios

## Qué hace
En `servicios_comerciales.html` y `servicios_publicos.html`, los bloques `list-inline-item` aparecen duplicados para versión desktop y mobile (`.d-sm-block.d-none` + `.d-block.d-sm-none`). Se unifican usando clases responsivas en un solo bloque.

## Criterios de aceptación

1. Los `list-inline-item` aparecen una sola vez en cada template.
2. El layout se ve igual en desktop y mobile que antes del cambio.
