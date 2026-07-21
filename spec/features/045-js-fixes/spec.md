# 045 — JS fixes (pdfjsLib guard, removeEventListener, jQuery mix)

## Qué hace
Corrige issues en JavaScript:

1. **`static/dist/js/pdf-form-preview.js:43`** — Usa `pdfjsLib` global sin verificar si está definido (si CDN falla, lanza ReferenceError)
2. **`static/dist/js/pdf-form-preview.js:152`** — `removeEventListener` no funciona porque la referencia es a una arrow function distinta
3. **`static/dist/js/forecast.js:1`** — Usa jQuery `$(document).ready()` pero el resto del file usa vanilla JS

## Criterios de aceptación
- `pdfjsLib` checked antes de usar
- `removeEventListener` funciona correctamente (guardar referencia)
- forecast.js usa `DOMContentLoaded` como el resto del proyecto
