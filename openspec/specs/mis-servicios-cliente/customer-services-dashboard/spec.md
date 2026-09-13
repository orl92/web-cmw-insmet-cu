---
change: mis-servicios-cliente
capabilities:
  - customer-services-dashboard
---

# customer-services-dashboard Specification

## Purpose

"Mis Servicios" lista TODAS las suscripciones del cliente con ribbon por estado y acciones contextuales; se unifica el formato de precio (helper `format_cup`) en catálogo, Mis Servicios, detail y admin.

## Requirements

### REQ-01: Helper único de precio `format_cup`

El filtro `format_cup` en `apps/core/templatetags/utils_filters.py` SHALL aceptar `Decimal|float|None` y retornar `str` con prefijo `$`, separador de miles `.` y decimales `,` (`$1.234,56`); `None`/vacío SHALL retornar `$0,00`. Los templates SHALL componer el período: `{{ price|format_cup }} CUP/{{ get_billing_period_display }}` → `$1.234,56 CUP/mes`. El mismo helper SHALL usarse en catálogo público, Mis Servicios, detail y admin; el método del modelo `get_price_per_period_display()` queda sin cambios.

#### Scenario: Precio con miles

- GIVEN price = 1234.56
- WHEN se renderiza `1234.56|format_cup`
- THEN el texto es `$1.234,56`

#### Scenario: Precio pequeño sin miles

- GIVEN price = 45.50 renderizado con `format_cup`
- WHEN se inspecciona el HTML
- THEN el texto es `$45,50` (decimal con coma, no `$45.50`)

#### Scenario: Composición con período

- GIVEN servicio `agrometeo` con price = 1234.56
- WHEN se renderiza catálogo, Mis Servicios o detail
- THEN aparece `$1.234,56 CUP/mes`

### REQ-02: Mis Servicios lista todas las suscripciones

`CommercialServicesListView` SHALL consultar `ServiceSubscription.objects.filter(customer=customer)` sin filtro de estado, ordenando `requested` → `pending` → `paid` → `expired` (Case/When) y luego `-start_date`.

#### Scenario: Todos los estados visibles

- GIVEN un cliente con subs en `requested`, `pending`, `paid` y `expired`
- WHEN se renderiza Mis Servicios
- THEN las cuatro aparecen en la lista

#### Scenario: Orden por prioridad de acción

- GIVEN subs `paid` y `requested` del mismo servicio
- WHEN se renderiza la lista
- THEN la fila `requested` aparece antes que la `paid`

### REQ-03: Ribbon dinámico por estado

Mis Servicios SHALL renderizar el ribbon según `status_display` vía `status_ribbon|get_item` (dict `STATUS_RIBBONS` inyectado por la view): `activo → bg-green`, `pendiente de pago → bg-orange`, `solicitado → bg-blue`, `expirado → bg-red`. No SHALL hardcodear el ribbon "Activo".

#### Scenario: Ribbon correcto por estado

- GIVEN sub `paid` (status_display "activo")
- WHEN se renderiza el card
- THEN el ribbon contiene la clase `bg-green` y el texto "activo"

#### Scenario: Expired muestra ribbon rojo

- GIVEN sub `expired`
- WHEN se renderiza el card
- THEN el ribbon contiene `bg-red` y el texto "expirado"

### REQ-04: Acciones contextuales por estado

| Estado | Acciones |
|---|---|
| activo | Ver PDF certificado (modal, `ti ti-file-type-pdf`) |
| pendiente + QR | Ver factura (`ti ti-receipt`, `commercial:factura_download/<uuid>?inline=1`) + Pagar con QR (`ti ti-qrcode`, `home:payment`) |
| pendiente + transfer | Ver factura (`ti ti-receipt`, `commercial:factura_download/<uuid>?inline=1`) |
| pendiente + presencial | Ver factura (`ti ti-receipt`, `commercial:factura_download/<uuid>?inline=1`) |
| solicitado | Badge "En proceso", SIN botones |
| expirado | Solicitar (`ti ti-send`, `home:services_commercial_detail`) |

El botón "Ver factura" SHALL apuntar a `commercial:factura_download/<uuid>?inline=1` usando la factura más reciente de la suscripción (`subscription.invoices.order_by('-issue_date').first()`). El botón SHALL renderizarse SOLO si `subscription.invoices.exists()`. El icono de pago SHALL ser diferenciado: `ti-qrcode` para QR, `ti-building-bank` para transferencia, `ti-building-store` para presencial.

#### Scenario: Pending con QR ofrece factura y pago

- GIVEN sub `pending` con `payment_method` QR y al menos 1 factura
- WHEN se renderiza el card
- THEN hay botón "Ver factura" con URL `commercial:factura_download/<uuid>?inline=1`
- AND hay botón "Pagar con QR" con URL `home:payment`
- AND el icono de pago es `ti-qrcode`

#### Scenario: Pending sin facturas no muestra Ver factura

- GIVEN sub `pending` con `payment_method` QR sin facturas asociadas
- WHEN se renderiza el card
- THEN el botón "Ver factura" NO se renderiza

#### Scenario: Pending transfer usa icono bancario

- GIVEN sub `pending` con `payment_method` transfer y al menos 1 factura
- WHEN se renderiza el card
- THEN el botón "Ver factura" apunta a `commercial:factura_download/<uuid>?inline=1`
- AND el icono de pago es `ti-building-bank`

#### Scenario: Pending presencial usa icono tienda

- GIVEN sub `pending` con `payment_method` presencial y al menos 1 factura
- WHEN se renderiza el card
- THEN el botón "Ver factura" apunta a `commercial:factura_download/<uuid>?inline=1`
- AND el icono de pago es `ti-building-store`

#### Scenario: Solicitado sin botones

- GIVEN sub `requested`
- WHEN se renderiza el card
- THEN solo aparece el badge "En proceso"
- AND ningún botón de acción se renderiza

### REQ-05: Metadatos normalizados

El card de Mis Servicios SHALL mostrar los metadatos en líneas independientes `<div class="mb-2">` con icono `me-1` ANTES del texto, en orden DOM: rango de fechas, método de pago, categoría, período, precio. NO SHALL renderizarse en un único bloque `d-flex flex-wrap gap-2` apiñado; la metadata SHALL envolverse en un wrapper `d-flex flex-column flex-grow-1 text-secondary mb-3` para el pin vertical del card (decisión D1 del design: `flex-grow-1` absorbe el espacio libre del `card-body d-flex flex-column`; sin `mt-auto` en la metadata).

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

## Coverage Notes

- Sin cambios de modelo ni migraciones (solo display y consultas de lectura).
- REQ-01 y REQ-08 (admin) son transversales al `format_cup`; REQ-08 vive en la spec del cambio pero la implementación es el mismo filtro.
