# home-pdf-viewer Specification

## Purpose

Define a single, accessible PDF viewing component (preview + full-screen modal)
reused by every PDF-bearing home template, and the accompanying a11y/UI fixes for
services, satellites, index and maps. The component must expose accessible control
names, a text alternative for the rendered `<canvas>`, a download fallback, and
must not call the non-existent `loadPdf()` method.

## Requirements

### Requirement: Shared PDF Preview Partial

Every PDF-bearing home template MUST render its preview via
`templates/includes/home/pdf_preview.html` (not duplicated inline markup) and the
preview container MUST carry `data-pdf-url` so `PDFViewerManager.initializeAll()`
auto-initializes it. Per-template inline `PDFViewer` init scripts MUST be removed.

#### Scenario: Preview renders through the shared partial

- GIVEN a home template that shows a PDF (avisos, publications, today, tomorrow, weather, note)
- WHEN the template is rendered
- THEN the HTML SHALL contain `id="pdfPreviewContainer"` with a `data-pdf-url` attribute
- AND the HTML SHALL NOT contain a per-template `new PDFViewer({` init script

### Requirement: Accessible PDF Modal Controls

`templates/includes/home/pdf_modal.html` MUST provide an `aria-label` on each of the
five toolbar controls (`modalPrevPage`, `modalNextPage`, `modalZoomOut`, `modalZoomIn`,
`modalFitWidth`) and SHALL include a download-fallback `<a>` with an accessible name.

#### Scenario: Modal toolbar controls are named

- GIVEN the modal partial is rendered
- WHEN the HTML is inspected
- THEN `modalPrevPage` SHALL have `aria-label="Página anterior"`
- AND `modalNextPage` SHALL have `aria-label="Página siguiente"`
- AND `modalZoomOut` SHALL have `aria-label="Alejar"`
- AND `modalZoomIn` SHALL have `aria-label="Acercar"`
- AND `modalFitWidth` SHALL have `aria-label="Ajustar al ancho"`
- AND a download fallback link with a non-empty `aria-label` SHALL be present

### Requirement: Canvas Text Alternative

The `<canvas>` rendered by `PDFViewer.renderPage` (`static/dist/js/pdf-viewer.js:46-52`)
MUST expose `role="img"` and an `aria-label` identifying the page (e.g.
`Página N del documento`).

#### Scenario: Rendered canvas is labeled

- GIVEN a PDF page is rendered into a `<canvas>`
- WHEN the canvas element is inspected
- THEN it SHALL carry `role="img"`
- AND it SHALL carry an `aria-label` referencing the current page number

### Requirement: No Dead `loadPdf()` Calls

No home template SHALL call `window.viewer.loadPdf(...)`. PDF modal loading MUST be
delegated to `PDFViewerManager`'s `show.bs.modal` handler, which calls the real
`loadNewPDF` (`pdf-viewer.js:315`). (Verified: the dead calls exist only in
`services/public.html:135-136` and `services/commercial.html:142-143`; they are NOT
in `publications.html`.)

#### Scenario: Repo contains no loadPdf invocations

- GIVEN the full repository source
- WHEN a grep for `loadPdf(` over `*.html` and `*.js` is run
- THEN the result SHALL be empty

#### Scenario: Modal opens via manager delegation

- GIVEN a "Ver PDF" trigger button with `data-bs-target="#pdfModal"` and `data-pdf-url`
- WHEN the button is clicked and `show.bs.modal` fires
- THEN `PDFViewerManager.modalViewer.loadNewPDF(url, title)` SHALL run (not a `loadPdf` call)

### Requirement: Avisos Use Shared Partial and Page Header

`templates/layouts/avisos.html` MUST drop its inline duplicate modal (lines 92-137),
drop the `.markdown` wrapper (line 14) and the duplicate in-card `<h1>` (line 15),
and MUST use `pdf_preview.html` + `pdf_modal.html` with the `page_header` block.

#### Scenario: Avisos render is deduplicated and semantic

- GIVEN `avisos.html` is rendered
- WHEN the HTML is inspected
- THEN it SHALL contain `{% include 'includes/home/pdf_modal.html' %}` (no inline modal markup)
- AND the card body SHALL NOT carry the `markdown` class
- AND there SHALL be no second `<h1>` duplicating the `page_header` title

### Requirement: Publications Use Shared Partial

`apps/home/templates/pages/home/institution/publications.html` MUST NOT manually
instantiate `PDFViewer` per object (lines 101-107); it MUST use `pdf_preview.html`
with `data-pdf-url` so the manager auto-initializes.

#### Scenario: Publications preview auto-initializes

- GIVEN a publication with a PDF is rendered
- WHEN the HTML is inspected
- THEN each preview container SHALL carry `data-pdf-url`
- AND no `new PDFViewer({` init loop SHALL be present

### Requirement: Reports Use Page Header and Shared Partial

`apps/home/.../weather/today.html`, `tomorrow.html`,
`apps/home/.../commentaries/weather.html`, `note.html` MUST drop `.markdown` (line 10),
the duplicate `<h1>` (line 11) and the inline init `<script>`, using `page_header` +
the shared partials.

#### Scenario: Report render is semantic and unified

- GIVEN any of the four report templates is rendered
- WHEN the HTML is inspected
- THEN the card body SHALL NOT carry `markdown`
- AND the in-card `<h1>` SHALL be absent (title comes from `page_header`)
- AND `pdfPreviewContainer` with `data-pdf-url` SHALL be present

### Requirement: Services Use Tabler Pagination

`services/public.html` (lines 84-98) and `services/commercial.html` (lines 94-108)
MUST render pagination with the Tabler `.pagination > .page-item > .page-link`
component bound to Django `page_obj`, not manual `<a href="?page=…">` links.

#### Scenario: Tabler pagination markup present

- GIVEN a services page with `is_paginated` true is rendered
- WHEN the HTML is inspected
- THEN it SHALL contain `.pagination` with `.page-item` and `.page-link` elements
- AND it SHALL NOT contain a bare `<a href="?page=1">` inside `.pagination`

### Requirement: Services Titles Are Headings Not Links

`services/public.html` (lines 22-23) and `services/commercial.html` (lines 21-22)
MUST render the service/subscription title and summary as `<h3>`/`<p>` text, not as
`<a>` elements without `href`.

#### Scenario: No link-wrapped headings

- GIVEN a services page is rendered
- WHEN the HTML is inspected
- THEN it SHALL NOT contain `<h3><a>` or `<p><a>` wrapping the title/summary

### Requirement: Satellite Gallery Images Are Labeled

`apps/home/.../satellites/satellites.html` MUST give each gallery image anchor
(`role="img"` + `aria-label`, or an `<img alt>`) describing the satellite product;
decorative background `<div>`s SHALL be `aria-hidden`.

#### Scenario: Gallery anchors expose names

- GIVEN the satellites page is rendered
- WHEN the gallery anchors are inspected
- THEN each image anchor SHALL carry `role="img"` and a non-empty `aria-label`

### Requirement: Index UV SVG Is Accessible

`apps/home/.../index.html` MUST give the UV `<svg>` (lines 153-175) `role="img"` plus a
`<title>`/`<desc>`, with the repeated decorative arc `<path>`s marked `aria-hidden`.

#### Scenario: UV svg has an accessible name

- GIVEN the index page is rendered
- WHEN the UV `<svg>` is inspected
- THEN it SHALL carry `role="img"`
- AND it SHALL contain a `<title>` element describing the current UV value

### Requirement: Inline Styles Moved to CSS (index)

`index.html` MUST NOT use inline `style="height:…"` on `#chartdiv` (line 224) or
`#station-details` (line 233); those heights SHALL live in `forecast.css`.

#### Scenario: No inline chart height

- GIVEN the index page is rendered
- WHEN `#chartdiv` and `#station-details` are inspected
- THEN neither SHALL carry an inline `style` with `height`

### Requirement: Maps Noisy Comments Removed

`apps/home/.../models/maps.html` MUST NOT contain the commented-out `<script>` lines
for Bootstrap bundle (line 209) and FontAwesome (line 211).

#### Scenario: No commented script tags

- GIVEN `maps.html` source
- WHEN the file is inspected
- THEN it SHALL NOT contain `{# <script src=…bootstrap.bundle.min.js #}` nor the FontAwesome `{# … #}` comment

### Requirement: djlint Passes on Touched Templates

All templates modified by this change MUST pass `djlint . --reformat --check` and
`djlint . --lint`.

#### Scenario: Lint clean

- GIVEN the changed templates are saved
- WHEN `djlint . --reformat --check` and `djlint . --lint` run
- THEN both SHALL exit without errors
