---
change: mis-servicios-cliente
capabilities:
  - customer-menu-notifications
---

# customer-menu-notifications Specification

## Purpose

Badge "Mis Servicios" = `requested + pending` del cliente; `client_pending_actions` calculado en el path normal. Badges por estado en "Mis Servicios" (no en "Servicios Comerciales"); badge padre "Servicios" estilo Avisos en vez de dot animado.

## Requirements

### REQ-09: Contador y badge del menú

`menu_notifications()` SHALL calcular `client_pending_actions = client_requested_count + client_pending_count` en el path normal. El item "Mis Servicios" SHALL mostrarse con ≥1 suscripción en CUALQUIER estado; el badge SHALL mostrar `client_pending_actions` y ocultarse cuando es 0. Los badges por estado (`bg-blue-lt` para `requested`, `bg-orange-lt` para `pending`) SHALL mostrarse en "Mis Servicios" (NO en "Servicios Comerciales").

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

### REQ-10: Badge padre "Servicios" estilo Avisos

El toggle padre "Servicios" SHALL renderizar un `<span class="badge bg-red-lt ms-2">{{ total }}</span>` cuando `client_pending_actions > 0`, siguiendo el patrón de badge de Avisos. NO SHALL renderizar un dot animado.

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

## Coverage Notes

- El menú "Mis Servicios" se muestra con ≥1 suscripción en cualquier estado; el badge solo refleja `requested + pending`. Los badges por estado migraron desde "Servicios Comerciales" (hoy sin badges). El dot animado fue reemplazado por badge `bg-red-lt` estilo Avisos (`pulido-ui-servicios`).
