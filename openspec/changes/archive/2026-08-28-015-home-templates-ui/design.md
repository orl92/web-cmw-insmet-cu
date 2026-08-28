# Design: Unified Accessible PDF Viewer and Home Template UI Overhaul

## Technical Approach

Introduce one reusable viewer pair — `pdf_preview.html` (scrollable first-page
preview) and `pdf_modal.html` (full-screen paged reader) — and make every
PDF-bearing home template delegate to them. The existing `PDFViewerManager`
(`static/dist/js/pdf-viewer.js:343-444`) already auto-initializes previews whose
container id matches `#pdfPreviewContainer` or `[id^="pdfPreviewContainer-"]` **and**
carries `data-pdf-url`, and binds modal open to `loadNewPDF` via
`show.bs.modal` (`pdf-viewer.js:396-404`). The fix is therefore mostly
*de-duplication*: delete per-template inline init scripts and the duplicate inline
modal in `avisos.html`, set `data-pdf-url` on the shared containers, and add the
a11y attributes in one place (the partial + `renderPage`).

The dead `loadPdf()` calls are NOT in `publications.html` (verified by grep — that
file has no such call; it uses a manual `new PDFViewer(...).init()` at lines
101-107). They exist only in `services/public.html:135-136` and
`services/commercial.html:142-143`. Both service templates also hand-roll a
`window.viewer` that is redundant with the manager. Removing that block lets the
manager's `show.bs.modal` handler do the work, using the already-present
`data-pdf-url` / `data-pdf-title` attributes on the trigger buttons.

## Visual Signature (frontend-design lens)

One deliberate aesthetic risk: the **report/notice header** — a centered title +
"Departamento de Pronósticos" eyebrow + a thin accent rule — becomes the memorable
element carried identically across avisos, today, tomorrow, weather, note and
publications. Everything else stays disciplined Tabler.

### Compact Token System (read from current theme)

| Token | Value | Source |
|-------|-------|--------|
| `--c-surface` | `#ffffff` | card bg (`pdf-viewer.css`) |
| `--c-page` | `#f8f9fa` | modal viewer bg (`pdf-viewer.css:67`) |
| `--c-border` | `#dee2e6` | Tabler default border |
| `--c-ink` | `#1d273b` / `--tblr-body-color` | Tabler text |
| `--c-accent` | `#206bc4` | Tabler 1.4.0 primary (links, "Ver PDF" pill) |
| `--c-control` | `rgba(0,0,0,0.7)` | modal toolbar bg (`pdf-viewer.css:95`) |

- **Typography:** Tabler `Inter` (`--tblr-font-sans-serif`). Scale:
  title `1.5rem/600`, eyebrow `0.75rem/500` uppercase `text-secondary`, body
  `0.9375rem/400`, small `0.8125rem`.
- **Spacing:** reuse Tabler spacing (`mt-3`, `mb-4`, `gap-2`); no custom scale.
- **Signature rule:** a 2px `--c-accent` top rule on the report card header,
  reused nowhere else.

### Wireframe — improved aviso / reporte / publicación page

```
┌──────────────────────────────────────────────────────────────┐
│ page-header (layout)                                          │
│   pretitle: Pronósticos            title: Comentario del Tiempo│  ← page_header block
├──────────────────────────────────────────────────────────────┤
│ card                                                            │
│  ┌─ signature accent rule (2px #206bc4) ─────────────────────┐ │
│  │  Comentario del Tiempo — Prov. Camagüey   (h1, centered)   │ │
│  │  Departamento de Pronósticos               (eyebrow)        │ │
│  │  Válido hasta: 22/08 14:00                 (meta row)       │ │
│  └───────────────────────────────────────────────────────────┘ │
│  Resumen: …                                      (rendered text) │
│                                                                │
│  ┌─ pdf_preview.html ───────────────────────────────────────┐ │
│  │   [ scrollable canvas, role=img, aria-label ]             │ │
│  │   Páginas: 3 en total                                     │ │
│  │   [Descargar PDF] (aria-label, fallback link)            │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ● Autor • 22/08 14:00                                        │
│  [ Ver PDF ]  (opens pdf_modal.html)                          │
│ └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘

pdf_modal.html (fullscreen):
  header: title (pdfModalLabel)  [✕ aria-label=Close]
  body:
    [ canvas role=img aria-label="Página N de M" ]
    [Descargar PDF] (fallback, aria-label)
    toolbar(bottom, bg rgba(0,0,0,.7)):
      [‹ aria-label="Página anterior"]
      Página N de M  (aria-live=polite)
      [› aria-label="Página siguiente"]
      [− aria-label="Alejar"]  100%  [+ aria-label="Acercar"]
      [Ajustar aria-label="Ajustar al ancho"]
```

## Architecture Decisions

| Decision | Options | Tradeoff | Chosen |
|----------|---------|----------|--------|
| Viewer delivery | Shared partials vs per-template copy | Partials dedupe markup + a11y in one place; manager already supports auto-init. Per-template copy caused the drift/bugs. | Shared `pdf_preview.html` + `pdf_modal.html` |
| Modal open mechanism | Manager `show.bs.modal` vs manual `loadPdf` | Manager already implements it correctly via `loadNewPDF`; manual `loadPdf` is dead code. | Manager delegation; delete manual JS |
| a11y on canvas | `role=img`+`aria-label` in JS vs wrapper | Canvas has no HTML alt; only JS can set per-page label. | `renderPage` sets attrs |
| Services pagination | Tabler `.pagination` vs manual `<a>` | Tabler component gives correct a11y/semantics + `page_link` styling; manual `<a>` lacks `page-item`. | Tabler pagination |
| Page title | `page_header` block vs in-card `<h1>` | Layout already renders `{{ title }}`/`{{ parent }}`; duplicate `<h1>` is redundant + harms outline. | Use `page_header`, drop dup `<h1>` |

## Data Flow (PDF modal)

```
User clicks [Ver PDF] (data-bs-target=#pdfModal, data-pdf-url, data-pdf-title)
   │  Bootstrap fires show.bs.modal
   ▼
PDFViewerManager.setupModalEvents (pdf-viewer.js:396)
   │  reads data-pdf-url / data-pdf-title
   ▼
manager.modalViewer.loadNewPDF(url, title)   (pdf-viewer.js:315)
   │  sets modalPdfUrl, resets page/scale, updates pdfModalLabel
   ▼
loadPDF(true)  →  renderModalPage(1)  →  renderPage()
        │  canvas.setAttribute('role','img'); canvas.setAttribute('aria-label', …)
        ▼
<canvas> shown; toolbar controls carry aria-label; download fallback link present
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `templates/includes/home/pdf_preview.html` | New | Preview container w/ `data-pdf-url` + "Descargar PDF" fallback (`aria-label`). |
| `templates/includes/home/pdf_modal.html` | Modify | `aria-label` on `modalPrevPage/NextPage/ZoomOut/ZoomIn/FitWidth`; add download fallback `<a>`; keep `<canvas>` rendered by JS with alt. |
| `static/dist/js/pdf-viewer.js` | Modify | In `renderPage` (46-52) set `canvas.role="img"` + `aria-label="Página N del documento"`; optionally `aria-live` on page info. Keep `loadPDF`/`loadNewPDF`. |
| `templates/layouts/avisos.html` | Modify | Delete inline modal (92-137) → `{% include pdf_modal.html %}`; use `pdf_preview.html`; drop `.markdown` (14) + dup `<h1>` (15); delete redundant extrajs init. |
| `apps/home/.../institution/publications.html` | Modify | Replace manual `new PDFViewer().init()` loop (101-107) + inline preview markup with `pdf_preview.html`; keep `pdf_modal.html` include. |
| `apps/home/.../weather/today.html`, `tomorrow.html` | Modify | Drop `.markdown` (10), dup `<h1>` (11), inline script (82-103); use partials. |
| `apps/home/.../commentaries/weather.html`, `note.html` | Modify | Same as reports (10, 11, 82-93). |
| `apps/home/.../services/public.html` | Modify | Tabler `.pagination` (84-98); `<h3>`/`<p>` titles (22-23); delete `window.viewer`+`loadPdf` JS (111-140). |
| `apps/home/.../services/commercial.html` | Modify | Tabler `.pagination` (94-108); `<h3>`/`<p>` titles (21-22); delete `loadPdf` JS (120-147). |
| `apps/home/.../satellites/satellites.html` | Modify | Add `role="img"`+`aria-label` to the two gallery anchor groups (6-64, 69-107). |
| `apps/home/.../index.html` | Modify | UV `<svg>` `role="img"`+`<title>`/`<desc>` (153-175); enable amCharts a11y; move `style="height:…"` (224,233) to `forecast.css`. |
| `apps/home/.../models/maps.html` | Modify | Delete `{# … #}` commented scripts (209 bootstrap, 211 fontawesome). |

## Interfaces / Contracts

**`pdf_preview.html` (partial) API**
```django
{% include 'includes/home/pdf_preview.html' with pdf_url=warning.absolute_file_url|default:warning.file.url pdf_title=title %}
```
Renders:
```html
<div class="d-flex justify-content-center align-items-center flex-column">
  <div id="pdfPreviewContainer" class="pdf-container-mobile" data-pdf-url="{{ pdf_url }}">
    <div id="pdfPages" class="pdf-pages-container"></div>
  </div>
  <a href="{{ pdf_url }}" class="btn btn-sm btn-link mt-2"
     aria-label="Descargar PDF: {{ pdf_title }}">Descargar PDF</a>
</div>
```
The manager auto-inits any `#pdfPreviewContainer` / `[id^="pdfPreviewContainer-"]`
that carries `data-pdf-url` (`pdf-viewer.js:421-439`).

**`pdf_modal.html` (partial) contract** — same id set as today (`#pdfModal`,
`#modalPdfPages`, `#modalPrevPage`, …). Buttons gain `aria-label`; a download
fallback `<a id="modalDownloadLink" aria-label="Descargar PDF">` is added (JS sets
its `href` from the active `data-pdf-url`).

**`PDFViewer.renderPage` canvas a11y**
```js
canvas.setAttribute('role', 'img');
canvas.setAttribute('aria-label', `Página ${page.pageNumber} del documento`);
```

## Testing Strategy

Repo uses `strict_tdd`; template tests live in `apps/home/tests/`. Render each
affected view (or a minimal `RequestFactory`/Django test client GET) and assert:

| Layer | What to Test | Approach |
|-------|--------------|----------|
| Render | avisos/publications/today render the shared partials | Assert response contains `id="pdfPreviewContainer"` and `id="pdfModal"`. |
| A11y | Modal controls have accessible names | Assert `aria-label="Página anterior"` etc. present in rendered HTML for `pdf_modal.html`. |
| A11y | No dead `loadPdf` calls | Grep the rendered output (and repo) for `loadPdf(` → zero matches. |
| A11y | Satellite images labeled | Assert gallery anchors carry `role="img"` + `aria-label`. |
| A11y | UV svg labeled | Assert `<svg … role="img">` with a `<title>` in `index.html` render. |
| UI | Services use Tabler pagination | Assert `.pagination .page-item .page-link` present; no bare `class="pagination"` `<a href="?page=">`. |
| UI | Titles are headings | Assert no `<h3><a>` / `<p><a>` in services render. |
| Lint | djlint | `djlint . --reformat --check` + `djlint . --lint` on touched templates. |

## Threat Matrix

`N/A — no routing, shell, subprocess, VCS/PR automation, executable-file
classification, or process-integration boundary is changed.` This is a
template/static-JS refactor; no untrusted-input execution path is added. The only
behavior change is client-side PDF modal wiring (delegated to the existing,
already-shipping `PDFViewerManager`).

## Migration / Rollout

No migrations, no model/URL changes, no backend behavior change. After deploy,
`collectstatic` is required so the updated `pdf-viewer.js`/`pdf-viewer.css` are
served. Enable by merging the phased diffs.

## Rollback

`git checkout -- <touched templates> static/dist/js/pdf-viewer.js`; run
`collectstatic --link`. No schema/migration step.

## Open Questions

- Should `pdf_preview.html` default to rendering ALL pages (scroll) or only page 1
  (current `renderPreview` behavior)? Keep page-1 preview (current) unless user
  wants full scroll; the partial supports either by toggling `isPreview`.
- Confirm the amCharts 5 accessibility import path available in the bundled
  `dist/libs/amcharts` build before enabling the a11y module in `index.html`.
