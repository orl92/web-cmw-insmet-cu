# Delta for customer-services-dashboard

## MODIFIED Requirements

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

(Previously: botón apuntaba a `commercial:factura_list` (sin UUID ni inline); icono de pago genérico `ti-credit-card`)

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

## MODIFIED Requirements

### REQ-05: Metadatos normalizados

El card de Mis Servicios SHALL mostrar los metadatos en orden: rango de fechas (con icono calendario ANTES del texto), método de pago (con icono diferenciado), precio con `format_cup` + período. El precio NO SHALL incluir icono `ti-currency-dollar` (el helper `format_cup` ya antepone `$`).

(Previously: metadatos con orden y estructura variable; precio con `ti-currency-dollar` redundante)

#### Scenario: Calendario precede al rango

- GIVEN sub con rango 01/01/2026 - 31/03/2026
- WHEN se inspecciona el HTML del card
- THEN el icono de calendario aparece antes del texto del rango en el DOM

#### Scenario: Precio sin icono dollar

- GIVEN sub con precio 1234.56
- WHEN se renderiza el card
- THEN el precio se muestra como `$1.234,56 CUP/mes` sin icono `ti-currency-dollar`

#### Scenario: Layout orden fechas-pago-precio

- GIVEN sub con fechas, método de pago y precio
- WHEN se inspecciona el orden DOM de los metadatos
- THEN las fechas aparecen primero, luego el método de pago, luego el precio
