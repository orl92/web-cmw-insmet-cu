# Delta for customer-services-dashboard

## MODIFIED Requirements

### REQ-05: Metadatos normalizados

El card de Mis Servicios SHALL mostrar los metadatos en líneas independientes `<div class="mb-2">` con icono `me-1` ANTES del texto, en orden DOM: rango de fechas, método de pago, categoría, período, precio. NO SHALL renderizarse en un único bloque `d-flex flex-wrap gap-2` apiñado; el último bloque de metadata SHALL conservar las clases `mt-auto mb-3` para el pin vertical del card.

| Línea | Icono | Contenido |
|---|---|---|
| Fechas | `ti-calendar-month` | `{{ start_date|date:'d/m/Y' }} - {{ end_date|date:'d/m/Y' }}` |
| Pago (si `payment_method`) | `payment_method_icon` diferenciado | `get_payment_method_display` |
| Categoría | `ti-tag` | "Categoría:" + `<strong>get_service_category_display</strong>` |
| Período | `ti-calendar-event` | "Período:" + `<strong>get_billing_period_display</strong>` |
| Precio (solo `commercial`) | — | `display-6 fw-bold text-primary` SOLO el monto `format_cup`, sin sufijo "CUP/período" (el período tiene línea propia) |

El icono de fechas SHALL ser `ti-calendar-month` (resuelve la inconsistencia preexistente: el template renderizaba `ti-calendar` pero los tests asertaban `ti-calendar-month`). El precio NO SHALL incluir icono `ti-currency-dollar` (el helper `format_cup` ya antepone `$`). El icono de pago SHALL ser diferenciado vía `payment_method_icon`: `ti-qrcode` QR, `ti-building-bank` transferencia, `ti-building-store` presencial.

(Previously: metadatos en un único `<div class="d-flex flex-wrap gap-2 text-secondary mt-auto mb-3">` con fechas (icono `ti-calendar`), pago y precio `format_cup` + "CUP/período"; sin líneas de categoría ni período; sin precio destacado)

#### Scenario: Calendario precede al rango

- GIVEN sub con rango 01/01/2026 - 31/03/2026
- WHEN se inspecciona el HTML del card
- THEN el icono `ti-calendar-month` aparece antes del texto del rango en el DOM
- AND el rango se muestra como `01/01/2026 - 31/03/2026`

#### Scenario: Precio sin icono dollar ni duplicación de período

- GIVEN sub comercial con precio 1234.56
- WHEN se renderiza el card
- THEN el precio se muestra como `$1.234,56` sin icono `ti-currency-dollar`
- AND el monto NO va seguido de "CUP/período" (el período tiene su propia línea)

#### Scenario: Orden DOM fechas-pago-categoría-período-precio

- GIVEN sub con fechas, método de pago, categoría, período y precio
- WHEN se inspecciona el HTML del card
- THEN las líneas aparecen en orden DOM: fechas, método de pago, categoría, período, precio
- AND cada línea es un `<div class="mb-2">` independiente
- AND no existe un bloque `d-flex flex-wrap gap-2` de metadata apiñada

#### Scenario: Líneas de categoría y período con strong

- GIVEN sub comercial con categoría y período
- WHEN se inspecciona el HTML
- THEN la línea categoría contiene `ti-tag` y `<strong>` con `get_service_category_display`
- AND la línea período contiene `ti-calendar-event` y `<strong>` con `get_billing_period_display`

#### Scenario: Icono de pago diferenciado antes del texto

- GIVEN sub con `payment_method` QR
- WHEN se inspecciona la línea de pago
- THEN el icono `ti-qrcode` con `me-1` aparece ANTES del texto `get_payment_method_display`
- (Variants: transfer → `ti-building-bank`; presencial → `ti-building-store`)

#### Scenario: Sin método de pago se omite la línea

- GIVEN sub sin `payment_method`
- WHEN se renderiza el card
- THEN la línea de método de pago NO se renderiza en el DOM

#### Scenario: Precio destacado solo para servicios comerciales

- GIVEN sub cuyo service NO es `commercial`
- WHEN se renderiza el card
- THEN la línea de precio destacado NO se renderiza
- AND sí aparecen las líneas de fechas y período

## Tests a actualizar

`apps/home/tests/test_services_ui.py`:

- `test_metadata_layout_order_is_dates_payment_price` SHALL re-escopar la región metadata (el marcador `d-flex flex-wrap gap-2 text-secondary mt-auto mb-3` desaparece) y asertar el nuevo orden fechas → pago → categoría → período → precio.
- `test_calendar_icon_precedes_date_range_in_dom` SHALL seguir asertando `ti-calendar-month` (ya consistente; sin cambio de aserción).
- (Los tests de catálogo `test_catalog_category_badge_has_*` viven en la spec `home-public-services-layout`.)
