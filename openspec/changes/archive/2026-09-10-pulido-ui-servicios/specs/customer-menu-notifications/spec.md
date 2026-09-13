# Delta for customer-menu-notifications

## MODIFIED Requirements

### REQ-09: Contador y badge del menú

`menu_notifications()` SHALL calcular `client_pending_actions = client_requested_count + client_pending_count` en el path normal. El item "Mis Servicios" SHALL mostrarse con ≥1 suscripción en CUALQUIER estado; el badge SHALL mostrar `client_pending_actions` y ocultarse cuando es 0. Los badges por estado (`bg-blue-lt` para `requested`, `bg-orange-lt` para `pending`) SHALL mostrarse en "Mis Servicios" (NO en "Servicios Comerciales").

(Previously: badges por estado estaban en "Servicios Comerciales"; sin badge diferenciado por tipo en "Mis Servicios")

#### Scenario: Badge suma requested + pending

- GIVEN cliente con 1 sub `requested` y 1 `pending`
- WHEN se renderiza el menú
- THEN el badge "Mis Servicios" muestra "2"

#### Scenario: Menú visible con solo expirada

- GIVEN cliente con solo una sub `expired`
- WHEN se renderiza el menú
- THEN el item "Mis Servicios" aparece
- AND el badge no se muestra (contador 0)

#### Scenario: Badges diferenciados en Mis Servicios

- GIVEN cliente con 2 subs `requested` y 1 sub `pending`
- WHEN se renderiza el menú
- THEN "Mis Servicios" muestra badge `bg-blue-lt` con texto "2" para requested
- AND badge `bg-orange-lt` con texto "1" para pending

#### Scenario: Servicios Comerciales sin badges

- GIVEN cliente con subs en cualquier estado
- WHEN se renderiza el menú
- THEN "Servicios Comerciales" NO muestra badges de estado

## MODIFIED Requirements

### REQ-10: Badge padre "Servicios" estilo Avisos

El toggle padre "Servicios" SHALL renderizar un `<span class="badge bg-red-lt ms-2">{{ total }}</span>` cuando `client_pending_actions > 0`, siguiendo el patrón de badge de Avisos. NO SHALL renderizar un dot animado.

(Previously: dot animado `status-dot status-dot-animated bg-red` en el toggle padre)

#### Scenario: Badge padre visible con pendientes

- GIVEN request normal con subs `requested` + `pending` (acciones > 0)
- WHEN se renderiza el menú
- THEN el toggle "Servicios" muestra badge `bg-red-lt` con el total de acciones pendientes
- AND no hay dot animado

#### Scenario: Sin pendientes, sin badge padre

- GIVEN `client_pending_actions == 0`
- WHEN se renderiza el menú
- THEN el toggle "Servicios" NO muestra badge
- AND no hay dot animado

#### Scenario: Badge padre suma correctamente

- GIVEN cliente con 3 requested y 2 pending
- WHEN se renderiza el menú
- THEN el badge padre muestra "5"

## REMOVED Requirements

### REQ-10 (anterior): Dot animado funcional

(Reason: Reemplazado por badge `bg-red-lt` estilo Avisos en REQ-10 modificado)
(Migration: Tests `test_menu_dot_animated_shown_when_pending_actions` y `test_menu_dot_animated_hidden_without_pending_actions` deben actualizarse para asertar badge `bg-red-lt` en vez de dot animado)
