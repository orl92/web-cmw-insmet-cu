# Proposal: Unified Accessible PDF Viewer and Home Template UI Overhaul

## Intent

The home section renders weather reports, early-warning notices, scientific
publications, services, satellite galleries, the index dashboard and model maps
across ~12 templates. Each PDF-bearing template re-implements its own preview
markup, its own inline `PDFViewer` init script, and (in `avisos.html`) its own
copy of the modal — producing duplicated, divergent, and partly broken code.
Accessibility is also inconsistent: the shared modal's toolbar buttons have no
`aria-label`, the rendered `<canvas>` has no text alternative, and two service
templates call a **non-existent** `window.viewer.loadPdf()` method (the real
method is `loadPDF`/`loadNewPDF` in `static/dist/js/pdf-viewer.js`). The user
approved full scope ("los quiero todos"). This change introduces ONE shared,
accessible PDF viewer (preview partial + modal) and applies it — plus targeted
a11y/UI fixes — to every affected home template, under a single disciplined
visual signature.

## Scope

### In Scope
- New shared partial `templates/includes/home/pdf_preview.html` (preview container
  with `data-pdf-url` + download fallback).
- Extend `templates/includes/home/pdf_modal.html` with `aria-label` on all 5
  toolbar controls, a download-fallback link (accessible name), and an accessible
  `<canvas>` alternative.
- Refactor `static/dist/js/pdf-viewer.js`: add `role="img"` + `aria-label` to the
  rendered `<canvas>`; keep the working `loadPDF`/`loadNewPDF` methods; rely on
  `PDFViewerManager` `show.bs.modal` delegation so no template calls `loadPdf`.
- Apply the shared viewer to: `templates/layouts/avisos.html`,
  `apps/home/templates/pages/home/institution/publications.html`,
  `apps/home/templates/pages/home/weather/{today,tomorrow}.html`,
  `apps/home/templates/pages/home/commentaries/{weather,note}.html`.
- A11y/UI fixes in: `services/public.html`, `services/commercial.html` (Tabler
  pagination instead of manual `<a>` links; titles as `<h*>` not `<a>`; drop dead
  `loadPdf` JS), `satellites/satellites.html` (alt/aria-label on gallery images),
  `index.html` (SVG UV `role`/`title`, amCharts a11y module, move inline styles to
  CSS), `models/maps.html` (remove noisy commented scripts).
- Transversal: remove misuse of the `.markdown` wrapper class, use the `page_header`
  block for page titles, unify render (`summary` vs `sanitize_html`).

### Out of Scope
- Changing `pdf-viewer.js` PDF.js rendering engine or worker.
- Backend views/models/URLs or migrations.
- Non-home apps (commercial, dashboard, etc.).
- Email templates under `*/emails/` (djlint-excluded by convention).

## Capabilities

### New Capabilities
- `home-pdf-viewer`: A single accessible PDF preview+modal component reusable by
  all home templates. Preview auto-initializes from `data-pdf-url` via
  `PDFViewerManager.initializeAll()`; modal loads via `loadNewPDF` on
  `show.bs.modal`. Toolbar controls expose accessible names; `<canvas>` carries a
  text alternative; a download link is the non-JS / screen-reader fallback.

### Modified Capabilities
- None beyond the home templates themselves; the JS class API (`loadPDF`,
  `loadNewPDF`, `PDFViewerManager`) is preserved, not changed in signature.

## Approach

0. **Establish the visual signature (frontend-design lens).** Define a compact
   token system (palette, type scale, spacing) read from the current Tabler theme
   and `pdf-viewer.css`. Spend the one aesthetic risk on the report/notice header
   treatment; keep everything else disciplined (see `design.md`).
1. **Create `pdf_preview.html`.** Renders the scrollable preview container
   (`#pdfPreviewContainer` + `#pdfPages`) carrying `data-pdf-url`, plus a
   "Descargar PDF" fallback `<a>` with `aria-label`. Templates drop their inline
   preview markup and inline init `<script>`.
2. **Extend `pdf_modal.html`.** Add `aria-label` to `modalPrevPage`,
   `modalNextPage`, `modalZoomOut`, `modalZoomIn`, `modalFitWidth`; add a
   download-fallback `<a>` (visible + screen-reader) and a `<canvas>` text
   alternative (rendered by JS). `avisos.html` deletes its inline duplicate modal.
3. **Refactor `pdf-viewer.js`.** In `renderPage` set `canvas.role="img"` and
   `canvas.aria-label` (e.g. `Página N del documento`). The `PDFViewerManager`
   already binds modal open → `loadNewPDF` (`pdf-viewer.js:396-404`), so service
   templates simply delete their manual `window.viewer` + `loadPdf` JS and keep
   their trigger buttons (`data-bs-target="#pdfModal"` + `data-pdf-url` +
   `data-pdf-title`).
4. **Apply to avisos/publications/reports.** Remove `.markdown`, drop the
   duplicate in-card `<h1>` (use the `page_header` block from
   `templates/layouts/home.html:14`), and switch to the shared partials.
5. **Services a11y.** Replace manual `.pagination` `<a href="?page=…">` with the
   Tabler `.pagination > .page-item > .page-link` component (public.html:84-98,
   commercial.html:94-108); change `<h3><a>{{title}}</a></h3>` / `<p><a>{{summary}}</a></p>`
   to real headings/text (public.html:22-23, commercial.html:21-22).
6. **Satellites / index / maps.** Add `role="img"` + `aria-label` to gallery
   anchors (satellites.html:6-107); give the UV `<svg>` `role="img"` +
   `<title>`/`<desc>` and enable the amCharts accessibility module, moving inline
   `style="height:…"` to CSS (index.html:153-233); delete the two `{# … #}`
   commented `<script>` lines (maps.html:209,211).

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `templates/includes/home/pdf_preview.html` | New | Shared preview partial (`data-pdf-url` + fallback link) |
| `templates/includes/home/pdf_modal.html` | Modified | `aria-label` on 5 controls; download fallback; canvas alt |
| `static/dist/js/pdf-viewer.js` | Modified | `canvas` a11y attrs in `renderPage` (line 46-52); keep `loadPDF`/`loadNewPDF` |
| `templates/layouts/avisos.html` | Modified | Drop inline modal (92-137), `.markdown` (14), dup `<h1>` (15); use partials |
| `apps/home/.../institution/publications.html` | Modified | Drop manual `PDFViewer` init (101-107); use partial |
| `apps/home/.../weather/today.html`, `tomorrow.html` | Modified | Drop `.markdown` (10), dup `<h1>` (11), inline script (82-103); use partial |
| `apps/home/.../commentaries/weather.html`, `note.html` | Modified | Same as reports above (10, 11, 82-93) |
| `apps/home/.../services/public.html` | Modified | Tabler pagination (84-98); `<h*>` titles (22-23); drop `loadPdf` JS (135-136) |
| `apps/home/.../services/commercial.html` | Modified | Tabler pagination (94-108); `<h*>` titles (21-22); drop `loadPdf` JS (142-143) |
| `apps/home/.../satellites/satellites.html` | Modified | `role="img"`+`aria-label` on gallery anchors (6-107) |
| `apps/home/.../index.html` | Modified | SVG `role`/`title` (153-175); amCharts a11y; move inline styles to CSS (224,233) |
| `apps/home/.../models/maps.html` | Modified | Remove commented scripts (209, 211) |
| `openspec/changes/015-home-templates-ui/specs/015-home-templates-ui/spec.md` | New | Delta spec |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Removing per-template inline `PDFViewer` init breaks preview render | Med | Preview auto-inits only when container carries `data-pdf-url`; verify every template sets it on the partial |
| `PDFViewerManager` auto-init double-binds modal events if two scripts load | Low | Delete per-template manager duplication; keep single `pdf-viewer.js` load |
| Tabler pagination markup mismatch with Django `page_obj` | Low | Map `page_obj` to `.page-item`/`.page-link` exactly as Tabler docs |
| >400 changed lines → review fatigue / large diff | High | Split into phased chained PRs (see `tasks.md`) |

## Rollback Plan

Each phase is independently revertible via `git checkout` on the touched template
+ `static/dist/js/pdf-viewer.js`. No migrations, no model/URL changes. Re-run
`djlint . --reformat --check` and `python manage.py test apps.home` after rollback.

## Dependencies

- Tabler 1.4.0 (layout/theme), PDF.js (already bundled), amCharts 5 (already bundled).
- `pdf-viewer.css` (`static/dist/css/pdf-viewer.css`) for viewer chrome.

## Success Criteria

- [ ] Every PDF-bearing home template uses `pdf_preview.html` + `pdf_modal.html`.
- [ ] Modal toolbar buttons (prev/next/zoom-/zoom+/fit) carry `aria-label`.
- [ ] Rendered `<canvas>` exposes `role="img"` + `aria-label`; modal has a download fallback link.
- [ ] No template calls `window.viewer.loadPdf(...)` (grep returns zero matches).
- [ ] Services use Tabler `.pagination`; titles are `<h*>` not `<a>`.
- [ ] Satellite gallery images expose `alt`/`aria-label`; UV `<svg>` has `role`/`title`.
- [ ] `djlint . --reformat --check` and `djlint . --lint` pass on all touched templates.
- [ ] `python manage.py test apps.home` passes (new a11y/render assertions).
