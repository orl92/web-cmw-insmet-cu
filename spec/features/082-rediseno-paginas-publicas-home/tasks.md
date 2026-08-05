# 082 — tasks

## Fase A — Partials base

- [ ] **T1** Paginacion Tabler: crear `templates/includes/pagination.html` (`ul.pagination`, enlaces primera/anterior/siguiente/ultima + `aria-label`). Aplicar en `services/public.html` y `services/commercial.html` (reemplaza `<div class="pagination">`).
- [ ] **T2** `includes/home/form_utc_fields.html`: partial con campo Fecha UTC (Litepicker) + select Hora UTC; parametros opcionales para campo extra (municipio/variable). Refactorizar `models/maps.html`, `models/meteogram.html`, `models/sounding.html` para usarlo (sin cambiar behavior JS; mantener `ids` datepicker/hour-select).
- [ ] **T3** `includes/home/pdf_scripts.html`: config worker PDF.js + init `PDFViewer` (param opcional `pdf_url`) + handler de clics `[data-bs-toggle="modal"][data-pdf-url]`. Sustituir el boilerplate en hoy/manana/comentario/nota/avisos/publicaciones/services (public/commercial). Mantener `pdf_modal.html` como unico modal.
- [ ] **T4** Partial de estado vacio compartido (variante sobre `empty_state.html`) para reemplazar el bloque `boy-refresh.webp` repetido (~6 paginas) con mensaje parametrizable.

## Fase B — Articulo / PDF

- [ ] **T5** `includes/home/weather_article.html`: partial de documento con `page-header` (pre-title + titulo `h2` + chip vigencia), datagrid metadata (Fecha/Hora/Autor con iconos), PDF embebido (barra con "Descargar" y "Pantalla completa"), footer autor/avatar, estado vacio. Parametros: `object` (weather_today/tomorrow/weather_commentary/weather_note), `title`, `pre_title`, `id`.
- [ ] **T6** Migrar `weather/today.html`, `weather/tomorrow.html`, `commentaries/weather.html`, `commentaries/note.html` al partial `weather_article` (incluye `data-pdf-title` en todos, hoy lo tenia y el resto no). Quitar `<h1>` de contenido (jerarquia V2).
- [ ] **T7** Modal PDF fullscreen (`pdf_modal.html`): anadir control "Descargar" (link al pdf actual del modal). Ajustar `pdf-viewer.js` solo si es indispensable (preferir data-attr + handler).

## Fase C — Avisos

- [ ] **T8** Rediseno `layouts/avisos.html`: card por `warning_type` (`early`/`storm`/`tropical_cyclone` → ribbon/card-status/badge con colores), `alert-important` de cabecera con el tipo, datagrid valido-hasta, resumen, PDF embebido (partial de T5/T7) y boton secundario. Reusar `pdf_scripts` y estado vacio.

## Fase D — Publicaciones

- [ ] **T9** `institution/publications.html`: entrada destacada (ultima) + grid de cards (icono PDF/portada, autor, fecha, institucion, "Leer PDF" via modal, "Descargar" via `publications:pdf`). Mantener `object.pdf` (campo unificado).
- [ ] **T10** Limpiar init `PDFViewer` muerto para `pdfPreviewContainer-N` en `institution/publications.html` (V7); dejar solo el handler modal de `pdf_scripts`.

## Fase E — Markup / accesibilidad

- [ ] **T11** `<a>` sin `href` en `services/public.html` y `services/commercial.html` → `<h3>`/`<p>` (o enlace real a detalle si aplica) (V1).
- [ ] **T12** Estilos inline recurrentes → utilidades/partial CSS (`object-fit`, alturas, `max-width`) en tarjetas de servicios y `qr.html` (V3).
- [ ] **T13** Reemplazar `onclick` inline y `alert()` en `models/maps.html` (toast) y `payment/qr.html` (`shareLink`) por listeners; `aria-live` en toasts (V4).
- [ ] **T14** Limpiar `{% static '' %}` y scripts comentados en `models/maps.html` y `models/meteogram.html` (V5).
- [ ] **T15** `payment/qr.html`: reducir duplicacion desktop/movil si es seguro; `aria-label` en `satellites.html` (V6).

## Verificacion y cierre

- [ ] **T16** `python manage.py check`; render por test client (con `ALLOWED_HOSTS` con `testserver`) de: index, tiempo hoy/manana, comentario, nota, avisos (3 tipos), publicaciones, satellites, maps, meteogram, sounding, qr, servicios (public/commercial/public_detail). 200 con y sin datos; sin `<h1>` duplicado; boton de suscripcion sigue visible (regresion B1).
- [ ] **T17** Suite completa OK; revision del diff (no tocar dos veces el mismo archivo fuera de fases).
- [ ] **T18** Actualizar `spec/constitution/roadmap.md` (mover 082 a "Hecho") y commit descriptivo (082).
