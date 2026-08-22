# Tasks: Unified Accessible PDF Viewer and Home Template UI Overhaul

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~620 (12 templates + JS + 2 partials + CSS + tests) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | One PR per phase (1-9), or batch 1-4 / 5-8 / 9 |
| Delivery strategy | ask-on-risk |
| Chain strategy | chained |
| 400-line budget risk | High |

Decision needed before apply: No (user approved full scope)
Chained PRs recommended: Yes
Chain strategy: chained
400-line budget risk: High

## Phase 1: Viewer partial + JS refactor + a11y  (~140 lines)

- [x] 1.1 Create `templates/includes/home/pdf_preview.html`: scrollable preview
      container (`#pdfPreviewContainer` + `#pdfPages`) carrying `data-pdf-url`, plus
      a "Descargar PDF" fallback `<a>` with `aria-label` (takes `pdf_url`, `pdf_title`).
- [x] 1.2 Extend `templates/includes/home/pdf_modal.html`: add `aria-label` to
      `modalPrevPage`, `modalNextPage`, `modalZoomOut`, `modalZoomIn`, `modalFitWidth`;
      add a download-fallback `<a id="modalDownloadLink" aria-label="Descargar PDF">`
      (JS sets its `href` from active `data-pdf-url`).
- [x] 1.3 In `static/dist/js/pdf-viewer.js` `renderPage` (lines 46-52) set
      `canvas.setAttribute('role','img')` and
      `canvas.setAttribute('aria-label', 'Página N del documento')`; set modal page
      info as `aria-live="polite"`; wire `modalDownloadLink.href` in `loadNewPDF`.
- [x] 1.4 Keep real methods `loadPDF` (`pdf-viewer.js:90`) and `loadNewPDF`
      (`pdf-viewer.js:315`); do NOT introduce `loadPdf`.

## Phase 2: Avisos  (~70 lines)

- [x] 2.1 In `templates/layouts/avisos.html` replace inline modal (lines 92-137)
      with `{% include 'includes/home/pdf_modal.html' with modal_title=title %}`.
- [x] 2.2 Replace per-warning preview markup (lines 33-44) with
      `{% include 'includes/home/pdf_preview.html' with pdf_url=… pdf_title=… %}`.
      Unique ids preserved via optional `preview_suffix=forloop.counter`
      (`pdfPreviewContainer-N` / `pdfPages-N`), as expected by the manager.
- [x] 2.3 Remove `.markdown` from `card-body` (line 14) and the duplicate `<h1>`
      (line 15); rely on the `page_header` block (`home.html:14`).
- [x] 2.4 Delete the redundant init listener from the `extrajs` block — the manager
      auto-runs on `DOMContentLoaded`. Library `<script>` tags + `workerSrc` config
      are kept: no layout loads them globally, so removing them would break PDFs.

## Phase 3: Publicaciones  (~40 lines)

- [x] 3.1 In `apps/home/templates/pages/home/institution/publications.html` replace
      the manual `new PDFViewer({…}).init()` loop (lines 101-107) and inline preview
      markup (lines 34-42) with `pdf_preview.html` (container carries `data-pdf-url`).
- [x] 3.2 Keep the existing `pdf_modal.html` include (line 88); ensure the
      download-fallback link renders.

## Phase 4: Reportes (today / tomorrow / weather / note)  (~120 lines)

- [x] 4.1 `apps/home/.../weather/today.html`: drop `.markdown` (10), duplicate `<h1>`
      (11), inline init `<script>` (82-103); use `pdf_preview.html` + `pdf_modal.html`.
- [x] 4.2 `apps/home/.../weather/tomorrow.html`: same edits (10, 11, 82-93).
- [x] 4.3 `apps/home/.../commentaries/weather.html`: same edits (10, 11, 82-93).
- [x] 4.4 `apps/home/.../commentaries/note.html`: same edits (10, 11, 82-92).
- [x] 4.5 Render `summary`/`sanitize_html` consistently; keep `page_header` title.

## Phase 5: Servicios (public + commercial)  (~90 lines)

- [x] 5.1 `services/public.html`: replace manual `.pagination` `<a href="?page=…">`
      (84-98) with Tabler `.pagination > .page-item > .page-link` bound to `page_obj`.
- [x] 5.2 `services/public.html`: change `<h3 class="mb-0"><a>{{service.title}}</a></h3>`
      and `<p><a>{{service.summary}}</a></p>` (22-23) to `<h3>`/`<p>` (no `<a>`).
- [x] 5.3 `services/public.html`: delete the `window.viewer` + `loadPdf` JS block
      (111-140); manager handles modal via `data-pdf-url`/`data-pdf-title`.
- [x] 5.4 `services/commercial.html`: Tabler pagination (94-108); `<h3>`/`<p>` titles
      (21-22); delete `loadPdf` JS (120-147).

## Phase 6: Satélites  (~30 lines)

- [x] 6.1 `apps/home/.../satellites/satellites.html`: add `role="img"` + `aria-label`
      to the two `data-fslightbox` gallery anchor groups (6-64, 69-107); move caption
      text into `aria-label` (decorative background divs get `aria-hidden`).

## Phase 7: Index  (~50 lines)

- [x] 7.1 `apps/home/.../index.html`: give the UV `<svg>` (153-175) `role="img"` +
       `<title>`/`<desc>`; mark the repeated decorative arcs `aria-hidden="true"`.
- [x] 7.2 amCharts 5 accessibility module NOT enabled: bundled dist has no ESM
       accessibility module path and no `enableFeature` API; left a note in extrajs.
- [x] 7.3 Move inline `style="height:450px;"` from `#chartdiv` (224) and
       `#station-details` (233) into `forecast.css` as utility classes.

## Phase 8: Maps  (~10 lines)

- [x] 8.1 `apps/home/.../models/maps.html`: delete the two `{# … #}` commented
       `<script>` lines (209 bootstrap bundle, 211 fontawesome).

## Phase 9: Verification  (tests ~70 lines)

- [ ] 9.1 Add `apps/home/tests/` render assertions: avisos/publications/today contain
      `pdfPreviewContainer` + `pdfModal`; `pdf_modal.html` controls carry
      `aria-label="Página anterior"` etc.
- [ ] 9.2 Grep-based assertion: rendered output (and repo) contains zero `loadPdf(`.
- [ ] 9.3 Assertion: satellite gallery anchors carry `role="img"`; UV `<svg>` carries
      `role="img"` + `<title>`.
- [ ] 9.4 Assertion: services render uses `.pagination .page-item .page-link` and has
      no `<h3><a>` / `<p><a>`.
- [ ] 9.5 Run `djlint . --reformat --check` and `djlint . --lint` on all touched
      templates — both pass.
- [ ] 9.6 Run `python manage.py test apps.home` — all pass.
- [ ] 9.7 Run `python manage.py check` — no system check errors.

## Phase 10: Commit

- [ ] 10.1 Commit per phase with a conventional message referencing `015-home-templates-ui`
      (e.g. `feat(home): unified accessible pdf viewer partial (015-home-templates-ui)`).
