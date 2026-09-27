# Delta for home-public-services-layout

## MODIFIED Requirements

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
