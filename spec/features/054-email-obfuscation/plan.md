# Plan — Feature 054

## Enfoque técnico

- Usar ofuscación por entity encoding + inversión JS: almacenar el email codificado en un atributo `data-*` y decodificarlo con JS en cliente.
- No requiere cambios de modelo, URL ni base de datos.

## Archivos

| Archivo | Cambio |
|---------|--------|
| `templates/pages/home/institucion/publicaciones/publicaciones.html` | Ofuscar `{{ object.author.email }}` |
| (opcional) `static/dist/js/publications.js` | JS para decodificar email en cliente |
