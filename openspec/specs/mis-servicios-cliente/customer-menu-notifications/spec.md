---
change: mis-servicios-cliente
capabilities:
  - customer-menu-notifications
---

# customer-menu-notifications Specification

## Purpose

Badge "Mis Servicios" = `requested + pending` del cliente; `client_pending_actions` calculado en el path normal (dot animado funcional).

## Requirements

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

## Coverage Notes

- El menú "Mis Servicios" se muestra con ≥1 suscripción en cualquier estado; el badge solo refleja `requested + pending`.
