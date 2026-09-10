# home-public-services-layout Specification

## Purpose

Define the public listing layout for services: each public service card presents the image and the PDF trigger side by side in two `col-md-6` columns, following the `core/site/settings.html` pattern. The PDF trigger SHALL keep opening the shared `#documentPdfModal` and SHALL preserve `data-pdf-url` and `data-pdf-title`.

## Requirements

### Requirement: Two-column image and PDF layout

`apps/home/templates/pages/home/services/public.html` SHALL render each public service card body so the image and the PDF section sit side by side in a `row` with two `col-md-6` columns (image left, PDF right), mirroring the settings layout. The image SHALL remain the banner/thumbnail; the PDF SHALL be exposed as a "Ver PDF" trigger.

#### Scenario: Card renders two columns

- GIVEN `public.html` is rendered for a public service with an image and a PDF
- WHEN the card body HTML is inspected
- THEN it SHALL contain a `row` with two `col-md-6` columns
- AND the first column SHALL contain the image
- AND the second column SHALL contain the "Ver PDF" trigger

#### Scenario: Service without PDF still renders in one column

- GIVEN a public service without a PDF is rendered
- WHEN the card body HTML is inspected
- THEN the "Sin PDF" fallback SHALL be present
- AND the layout SHALL NOT emit a broken or empty PDF column

### Requirement: PDF trigger keeps modal data attributes

The "Ver PDF" trigger SHALL open `#documentPdfModal` via `data-bs-toggle="modal" data-bs-target="#documentPdfModal" data-pdf-url` and SHALL preserve `data-pdf-title`. It SHALL NOT open the PDF in a new tab.

#### Scenario: Trigger exposes data-pdf-url and data-pdf-title

- GIVEN `public.html` is rendered for a public service with a PDF
- WHEN the HTML is inspected
- THEN the trigger SHALL contain a `data-pdf-url=` pointing to the service PDF URL
- AND the trigger SHALL contain `data-pdf-title` equal to the service title
- AND the response SHALL NOT contain `target="_blank"` pointing to a file URL

### Requirement: Commercial services public card is state-neutral

`commercial_public.html` SHALL renderizar el card del catálogo comercial como imagen, título, badge de categoría, precio `format_cup`, summary truncado, código discreto (si existe) y un único botón ("Solicitar" logueado / "Iniciar sesión" anónimo con `ti ti-login`). NO SHALL renderizar ribbons por estado ni botones por estado, y NO SHALL consumir `user_subscriptions` ni `now` del contexto.

#### Scenario: Card sin ribbon ni botones de estado

- GIVEN `commercial_public.html` con cliente logueado con sub `paid`
- WHEN se inspecciona el HTML del card
- THEN no hay clases `bg-green`/`bg-orange`/`bg-blue`/`bg-red`
- AND el único control es "Solicitar"

#### Scenario: Card anónimo sin ribbon

- GIVEN usuario anónimo
- WHEN se inspecciona el HTML
- THEN el único control es "Iniciar sesión" sin ribbon

## Coverage Notes

- Layout change is limited to `public.html`; commercial services listing is out of scope.
- The shared `documentPdfModal` partial (`includes/home/document_pdf_modal.html`) and its in-modal download link are preserved unchanged.
