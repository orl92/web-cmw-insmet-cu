# Plan — 045-js-fixes

## Enfoque técnico
1. Agregar `if (typeof pdfjsLib !== 'undefined')` antes de usar `pdfjsLib.getDocument()`
2. Guardar referencia a `handleFileSelect` en el constructor para que `removeEventListener` funcione
3. Cambiar `$(document).ready()` por `document.addEventListener('DOMContentLoaded', ...)` en forecast.js

## App(s) modificadas
- static/dist/js/pdf-form-preview.js
- static/dist/js/forecast.js
