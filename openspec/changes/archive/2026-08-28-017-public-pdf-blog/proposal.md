# Change 017-public-pdf-blog

## Intent
Uniformar la presentación pública de documentos PDF como tarjetas estilo blog, eliminar la página de detalle público de publicaciones, y llevar el botón "Ver PDF" del dashboard al mismo partial + modal ya usado en el resto del sitio.

## Motivation
Tras el change 016 (que unificó el modal PDF), las áreas públicas aún son inconsistentes: `avisos` renderiza un título hardcodeado "Aviso meteorológico" + un badge de tipo de aviso y deja una columna en blanco enorme; `publications` usa una card custom con una página "Ver detalle" que el usuario no necesita; y el dashboard sigue abriendo PDFs en una pestaña nueva con `<a target="_blank">`. El usuario quiere una experiencia única, estilo blog, con modal al hacer clic, en todo el sitio.

## Scope
- Plantillas públicas: `templates/layouts/avisos.html`, `apps/home/templates/pages/home/institution/publications.html`, secciones de home para avisos/publicaciones.
- Plantillas de detalle del dashboard: `apps/commercial/templates/pages/commercial/certificate/detail.html`, `apps/meteo/templates/pages/meteo/weather_report/_detail.html`, `apps/publications/templates/pages/publications/detail.html`.
- Modelo: `apps.meteo.models.Warning` gana un campo `title`.

## Out of scope
- Internals del motor PDF.js; auth; cambios de API.

## Decisions (confirmadas por el usuario)
- Agregar campo `Warning.title` (modelo + migración; migraciones no versionadas / gitignored).
- Nuevo change 017 (016 queda abierto para archivar luego).
- Home usa grid responsivo (`row-deck`) para las tarjetas blog.
- La card de publicaciones elimina el bloque de email del autor.
- Borrar `pdf-form-preview.js` / `pdf-form-preview.css` (código muerto, huérfano).

## Acceptance Criteria
1. Card de avisos: sin badge, sin título "Aviso meteorológico", sin columna en blanco; usa `document_card.html`.
2. Lista de publicaciones: `document_card.html` en grid responsivo; sin "Ver detalle"/public_detail; sin email.
3. Home: avisos + publicaciones se muestran como tarjetas blog en grid responsivo.
4. Vista/url/template/test de `public_detail` eliminados; sin referencia colgante `publications:public_detail`.
5. Detalle de dashboard usa `document_card.html` + un `document_pdf_modal.html`; sin `<a target="_blank">Ver PDF</a>` crudo.
6. `pdf-form-preview.js` + `.css` borrados; cero referencias.
7. `Warning.title` existe; el título de la card cae back a `summary` cuando está vacío.
8. Suite de tests completa pasa; djlint reformat+lint limpio; `manage.py check` limpio.
