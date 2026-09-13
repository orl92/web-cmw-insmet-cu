# Delta for home-public-services-layout

## MODIFIED Requirements

### Requirement: Commercial services public card is state-neutral

`commercial_public.html` SHALL renderizar el card del catálogo comercial como imagen, título, badge de categoría con icono diferenciado, precio `format_cup`, summary truncado y un único botón ("Solicitar" logueado / "Iniciar sesión" anónimo con `ti ti-login`). NO SHALL renderizar ribbons por estado ni botones por estado, y NO SHALL consumir `user_subscriptions` ni `now` del contexto. El precio NO SHALL incluir icono `ti-currency-dollar` (el helper `format_cup` ya antepone `$`). NO SHALL renderizar el bloque "Código:" con icono `ti-hash`. El badge de categoría SHALL usar icono diferenciado: `ti-cloud` para pronóstico, `ti-plant` para agrometeo.

(Previously: card incluía `ti-currency-dollar` en precio, bloque "Código:" con `ti-hash`, badge de categoría sin icono diferenciado)

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
