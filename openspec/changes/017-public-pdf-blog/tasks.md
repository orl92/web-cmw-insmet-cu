# Tasks — 017-public-pdf-blog

- [ ] 1. Agregar campo `title` a `Warning`; makemigrations + migrate (migrations gitignored).
- [ ] 2. `avisos.html`: quitar badge + título hardcodeado; usar `document_card` con `title=warning.title|default:warning.summary`; arreglar columna en blanco.
- [ ] 3. `publications.html`: reemplazar card custom con `document_card` en `row row-deck`; quitar "Ver detalle" + bloque email; mantener un modal.
- [ ] 4. Home: envolver secciones de avisos + publicaciones en grid responsivo (row-deck).
- [ ] 5. Remover public_detail: template, vista, URL, test y referencias colgantes.
- [ ] 6. Dashboard sweep: `commercial/certificate/detail.html`, `meteo/weather_report/_detail.html`, `publications/detail.html` → `document_card` + un modal.
- [ ] 7. Borrar `pdf-form-preview.js` + `pdf-form-preview.css`; confirmar cero refs.
- [ ] 8. Tests: borrar/ajustar public_detail + título/badge de avisos; agregar tests blog-card + modal dashboard; suite completa verde.
- [ ] 9. djlint reformat+lint; `manage.py check`; commit.
