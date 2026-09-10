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
| pendiente + QR | Ver factura (`ti ti-receipt`, `commercial:factura_list`) + Pagar con QR (`ti ti-qrcode`, `home:payment`) |
| pendiente + transfer/presencial | Ver factura (`ti ti-receipt`, `commercial:factura_list`) |
| solicitado | Badge "En proceso", SIN botones |
| expirado | Solicitar (`ti ti-send`, `home:services_commercial_detail`) |

#### Scenario: Pending con QR ofrece factura y pago

- GIVEN sub `pending` con `payment_method` QR
- WHEN se renderiza el card
- THEN hay botones "Ver factura" y "Pagar con QR"
- AND sus URLs apuntan a `commercial:factura_list` y `home:payment`

#### Scenario: Solicitado sin botones

- GIVEN sub `requested`
- WHEN se renderiza el card
- THEN solo aparece el badge "En proceso"
- AND ningún botón de acción se renderiza

### REQ-05: Metadatos normalizados

El card de Mis Servicios SHALL mostrar el icono de calendario ANTES del rango de fechas, el precio con `format_cup` + período y el método de pago.

#### Scenario: Calendario precede al rango

- GIVEN sub con rango 01/01/2026 - 31/03/2026
- WHEN se inspecciona el HTML del card
- THEN el icono de calendario aparece antes del texto del rango en el DOM

## Coverage Notes

- Sin cambios de modelo ni migraciones (solo display y consultas de lectura).
- REQ-01 y REQ-08 (admin) son transversales al `format_cup`; REQ-08 vive en la spec del cambio pero la implementación es el mismo filtro.
