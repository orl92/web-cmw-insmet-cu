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

`commercial_public.html` SHALL renderizar el card del catálogo comercial como imagen, título, metadata en líneas independientes, summary truncado y un único botón ("Solicitar" logueado / "Iniciar sesión" anónimo con `ti ti-login`). NO SHALL renderizar ribbons por estado ni botones por estado, y NO SHALL consumir `user_subscriptions` ni `now` del contexto. El precio NO SHALL incluir icono `ti-currency-dollar` (el helper `format_cup` ya antepone `$`). NO SHALL renderizar el bloque "Código:" con icono `ti-hash`. El badge de categoría SHALL usar icono diferenciado: `ti-cloud` para pronóstico, `ti-plant` para agrometeo.

La metadata SHALL renderizarse en líneas independientes `<div class="mb-2">` (patrón de `service_detail.html` L25-32), con icono `me-1` ANTES del texto:

| Línea | Icono | Contenido |
|---|---|---|
| Categoría | `ti-cloud`/`ti-plant` | "Categoría:" + `<strong>{{ service.get_service_category_display }}</strong>` |
| Período | `ti-calendar-event` | "Período:" + `<strong>{{ service.get_billing_period_display }}</strong>` |
| Precio | — | `display-6 fw-bold text-primary` con monto `format_cup` + `<small class="text-secondary">CUP/{{ service.get_billing_period_display }}</small>` |

La metadata NO SHALL renderizarse en bloques `d-flex flex-wrap gap-2` apiñados (L30-41 actuales); el último bloque de metadata SHALL conservar las clases `mt-auto mb-3` para el pin vertical del card.

(Previously: categoría y precio en bloques `d-flex flex-wrap gap-2` apiñados, sin línea de período propia ni precio destacado)

#### Scenario: Card sin ribbon ni botones de estado

- GIVEN `commercial_public.html` con cliente logueado con sub `paid`
- WHEN se inspecciona el HTML del card
- THEN no hay clases `bg-green`/`bg-orange`/`bg-blue`/`bg-red`
- AND el único control es "Solicitar"

#### Scenario: Card anónimo sin ribbon

- GIVEN usuario anónimo
- WHEN se inspecciona el HTML
- THEN el único control es "Iniciar sesión" sin ribbon

#### Scenario: Precio sin icono dollar

- GIVEN servicio con precio 1234.56
- WHEN se renderiza el catálogo público
- THEN el precio se muestra como `$1.234,56` sin icono `ti-currency-dollar`

#### Scenario: Sin bloque código

- GIVEN servicio con código asignado
- WHEN se renderiza el catálogo público
- THEN NO aparece el bloque "Código:" con icono `ti-hash`

#### Scenario: Badge categoría pronóstico con icono

- GIVEN servicio con categoría "Pronóstico"
- WHEN se renderiza el card
- THEN el badge de categoría contiene icono `ti-cloud`

#### Scenario: Badge categoría agrometeo con icono

- GIVEN servicio con categoría "Agrometeo"
- WHEN se renderiza el card
- THEN el badge de categoría contiene icono `ti-plant`

#### Scenario: Orden DOM categoría-período-precio

- GIVEN servicio comercial con categoría, período y precio
- WHEN se inspecciona la metadata del card
- THEN las líneas aparecen en orden DOM: categoría, período, precio
- AND cada línea es un `<div class="mb-2">` independiente
- AND no existe un único bloque `d-flex flex-wrap gap-2` de metadata apiñada

#### Scenario: Precio destacado display-6 con CUP/período

- GIVEN servicio con price = 1234.56 y período "mensual"
- WHEN se renderiza el catálogo público
- THEN el precio usa `display-6 fw-bold text-primary` y muestra el monto `$1.234,56`
- AND el `<small class="text-secondary">` contiene `CUP/mensual`

#### Scenario: Icono de categoría antes del label

- GIVEN servicio con categoría "pronostico"
- WHEN se inspecciona la línea de categoría
- THEN el icono `ti-cloud` con `me-1` aparece ANTES del texto "Categoría:"
- AND el label usa `<strong>{{ service.get_service_category_display }}</strong>`

## Tests a actualizar

`apps/home/tests/test_services_ui.py`: `test_catalog_category_badge_has_cloud_icon` y `test_catalog_category_badge_has_plant_icon` SHALL actualizarse para asertar el icono (`ti-cloud`/`ti-plant`) con `me-1` ANTES del label "Categoría:" en su línea `<div class="mb-2">` (hoy solo asertan presencia del icono en el HTML).
## Coverage Notes

- Layout change is limited to `public.html`; commercial services listing is out of scope.
- The shared `documentPdfModal` partial (`includes/home/document_pdf_modal.html`) and its in-modal download link are preserved unchanged.
