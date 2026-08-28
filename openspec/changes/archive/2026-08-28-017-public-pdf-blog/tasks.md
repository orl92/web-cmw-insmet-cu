# Tasks — 017-public-pdf-blog

## Nota de reconciliación (archivo manual 2026-08-28)

Todas las tareas estaban completadas en código (commits `c0df070`, `6674e9d` y
afines) pero no se habían marcado `[x]`. Verificado por inspección de árbol:
`public_detail.html`, `test_public_detail.py`, `pdf-form-preview.js`/`.css`
eliminados; `avisos.html` usa `document_card.html` con `title`; cero refs
colgantes a `publications:public_detail`/`pdf-form-preview`. Se marcan `[x]` para
cerrar el ciclo SDD (archivo manual porque `gentle-ai sdd-archive` está roto por
el bug sha256 vs SHA-1 en `sdd-attempt`).

- [x] 1. Agregar campo `title` a `Warning`; makemigrations + migrate (migrations gitignored).
- [x] 2. `avisos.html`: quitar badge + título hardcodeado; usar `document_card` con `title=warning.title|default:warning.summary`; arreglar columna en blanco.
- [x] 3. `publications.html`: reemplazar card custom con `document_card` en `row row-deck`; quitar "Ver detalle" + bloque email; mantener un modal.
- [x] 4. Home: envolver secciones de avisos + publicaciones en grid responsivo (row-deck).
- [x] 5. Remover public_detail: template, vista, URL, test y referencias colgantes.
- [x] 6. Dashboard sweep: `commercial/certificate/detail.html`, `meteo/weather_report/_detail.html`, `publications/detail.html` → `document_card` + un modal.
- [x] 7. Borrar `pdf-form-preview.js` + `pdf-form-preview.css`; confirmar cero refs.
- [x] 8. Tests: borrar/ajustar public_detail + título/badge de avisos; agregar tests blog-card + modal dashboard; suite completa verde.
- [x] 9. djlint reformat+lint; `manage.py check`; commit.
