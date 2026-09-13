---
change: mis-servicios-cliente
capabilities:
  - customer-services-dashboard
  - customer-menu-notifications
  - home-public-services-layout
  - commercial-service-categories
---

# mis-servicios-cliente Specification

## Purpose

"Mis Servicios" pasa a listar TODAS las suscripciones del cliente con ribbon por estado y acciones contextuales; el catálogo público pierde la lógica de estado (card limpia con badge de categoría, código discreto, precio formateado y botón único); se unifica el formato de precio (helper `format_cup`) en catálogo, Mis Servicios, detail y admin; se corrige el bug de `client_pending_actions` en el path normal (contador y dot del menú).

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

### REQ-06: Catálogo público sin lógica de estado

`commercial_public.html` SHALL renderizar imagen, título, badge de categoría, precio `format_cup`, summary truncado, código discreto (si existe) y un único botón. NO SHALL renderizar ribbons ni botones por estado, ni consumir `user_subscriptions`/`now` (eliminados de `PublicCommercialServicesListView`).

#### Scenario: Cliente con suscripción activa ve card limpio

- GIVEN cliente logueado con sub `paid` del servicio
- WHEN se renderiza el catálogo
- THEN no hay ribbon "Activo" ni botón "Solicitar de nuevo"
- AND el único control es "Solicitar"

#### Scenario: Anónimo ve botón de login

- GIVEN usuario anónimo
- WHEN se renderiza el catálogo
- THEN el único control es "Iniciar sesión" con icono `ti ti-login`

### REQ-07: Iconos en botones

Los botones SHALL usar: Pagar con QR `ti ti-qrcode`; Iniciar sesión `ti ti-login`; Ver relacionados `ti ti-eye`; submit del detail "Solicitar" `ti ti-send`; Cancelar `ti ti-x`; Ver factura `ti ti-receipt`; Ver PDF certificado `ti ti-file-type-pdf`.

#### Scenario: Iconos presentes en detail

- GIVEN el detail de servicio con submit y cancelar
- WHEN se inspecciona el HTML
- THEN el submit contiene `ti ti-send`
- AND el botón cancelar contiene `ti ti-x`

### REQ-08: Admin usa format_cup

`apps/commercial/templates/pages/commercial/service/list.html` SHALL reemplazar `floatformat:2` por `format_cup` en la celda de precio.

#### Scenario: Admin muestra $45,50

- GIVEN servicio comercial con price = 45.50
- WHEN se renderiza el listado admin
- THEN la celda Precio contiene `$45,50`
- AND el test de `test_views.py` aserta `$45,50` (no `$45.50`)

### REQ-09: Contador y badge del menú

`menu_notifications()` SHALL calcular `client_pending_actions = client_requested_count + client_pending_count` en el path normal (no solo en el `except`). El item "Mis Servicios" SHALL mostrarse con ≥1 suscripción en CUALQUIER estado; el badge SHALL mostrar `client_pending_actions` y ocultarse cuando es 0.

#### Scenario: Badge suma requested + pending

- GIVEN cliente con 1 sub `requested` y 1 `pending`
- WHEN se renderiza el menú
- THEN el badge "Mis Servicios" muestra "2"

#### Scenario: Menú visible con solo expirada

- GIVEN cliente con solo una sub `expired`
- WHEN se renderiza el menú
- THEN el item "Mis Servicios" aparece
- AND el badge no se muestra (contador 0)

### REQ-10: Dot animado funcional

El dot animado del menú SHALL renderizarse cuando `client_pending_actions > 0`, calculado en el path normal sin depender de una excepción previa.

#### Scenario: Dot visible con pendientes

- GIVEN request normal con subs `requested` + `pending` (acciones > 0)
- WHEN se renderiza el menú
- THEN el dot animado está presente

#### Scenario: Sin pendientes, sin dot

- GIVEN `client_pending_actions == 0`
- WHEN se renderiza el menú
- THEN no se renderiza el dot

### REQ-11: Submit del detail unificado

El submit del detail SHALL decir "Solicitar" (antes "Solicitar de nuevo"/"Aceptar") con `ti ti-send`. Se SHALL conservar la semántica in-flight: bloqueo ante sub `requested`/`pending` y alerta de vigencia cuando existe `paid` activa (la re-solicitud crea fila `requested` junto a la vigente).

#### Scenario: Submit unificado con paid activa

- GIVEN cliente con sub `paid` activa para el servicio
- WHEN el detail se renderiza (GET)
- THEN el submit dice "Solicitar"
- AND la alerta de vigencia hasta `end_date` se conserva

## Capability customer-services-dashboard

Capacidad NUEVA — cubre REQ-01, REQ-02, REQ-03, REQ-04, REQ-05 (REQ-01 y REQ-08 son transversales al `format_cup`).

## Capability customer-menu-notifications

Capacidad NUEVA — cubre REQ-09 y REQ-10.

## Capability home-public-services-layout

Delta sobre la spec vigente `openspec/specs/categoria-y-layout-servicios/home-public-services-layout/spec.md` — modifica su REQ "Commercial services page unaffected".

### Requirement: Commercial services public card is state-neutral

(Previously: "The commercial services listing layout SHALL remain unchanged", y el catálogo renderizaba ribbons y botones por estado.)

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

## Capability commercial-service-categories

Delta sobre la spec vigente `openspec/specs/categoria-y-layout-servicios/commercial-service-categories/spec.md` (contenido ADDED). Además SUPERSEDE dos REQ de la spec previa `openspec/specs/022-servicios-comerciales-por-tipo/commercial-service-categories/spec.md`: el escenario "existing ribbon for staff is preserved" (los ribbons del catálogo se eliminan; los controles staff "Editar"/"Nuevo servicio" se conservan) y la REQ "Pending subscription guidance without QR" (la guía de estado pendiente se traslada a Mis Servicios como acción "Ver factura").

### Requirement: Public card exposes category badge and discrete code

(New — ADDED sobre la spec vigente de commercial-service-categories.)

`commercial_public.html` SHALL renderizar el badge de categoría (`service.get_service_category_display()`: "Agrometeorológico"/"Pronóstico") y el `service.code` de forma discreta (p. ej. "Código: C200") solo si existe, como referencia para facturas.

#### Scenario: Badge y código visibles

- GIVEN servicio comercial con `service_category='agrometeo'` y code='C200'
- WHEN se renderiza el card público
- THEN aparece el badge "Agrometeorológico"
- AND el texto "Código: C200" está presente

#### Scenario: Sin código no se muestra etiqueta

- GIVEN servicio comercial sin `code`
- WHEN se renderiza el card público
- THEN no hay etiqueta "Código:"

## Coverage Notes

- Sin cambios de modelo ni migraciones (solo display y consultas de lectura).
- El menú "Mis Servicios" se muestra con ≥1 suscripción en cualquier estado; el badge solo refleja `requested + pending`.
- La semántica de re-solicitud (bloqueo in-flight + fila `requested` junto a la vigente + alerta del detail) se conserva de `reesolicitar-servicio-activo`; solo cambia el texto del submit a "Solicitar".
