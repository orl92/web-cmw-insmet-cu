# Propuesta: Reesolicitar servicio con suscripción activa

## Motivación

Un cliente con suscripción comercial activa (`paid`, `end_date` futuro) no puede re-solicitar el mismo servicio: `ServiceDetailView` bloquea toda fila no expirada. `SubscriptionRenewView` ya crea una fila `requested` junto a la `paid` y el modelo no tiene constraint único `(customer, service)`. Objetivo: replicar esa semántica — fila nueva `requested`, la vigente intacta hasta que se pague.

## Alcance

**Dentro**: relajar el bloqueo del detalle a solo `requested`/`pending`; resolver estado por servicio en las vistas; `service_detail.html` (alerta + formulario + botón "Solicitar de nuevo" con activa); `commercial_public.html` (botón "Solicitar de nuevo" bajo ribbon "Activo"); tests en `apps/home/tests/test_services_ui.py` y `apps/commercial/tests/test_views.py`.

**Fuera**: flujo staff (`SubscriptionCreateView` sin guardas, solo tests); cambio de esquema (sin migraciones); facturación de la fila nueva (queda como hoy); vínculo/log de renovación.

## Capacidades

**Nuevas**: `service-re-request` — el cliente puede re-solicitar un servicio con suscripción activa; se crea `requested` sin tocar la vigente; solo una solicitud en trámite bloquea.

**Modificadas**: None — `commercial-service-categories` y `home-public-services-layout` no cambian.
Solución propuesta

- `form_valid`: `.exclude(payment_status='expired')` → `payment_status__in=['requested', 'pending']`; si existe, warning actual + redirect; si no, crear `requested` como hoy.
- Detalle: `existing_subscription` se divide en `in_flight_subscription` (requested/pending) y `active_subscription` (`paid` + `is_active`).
- `service_detail.html`: `in_flight` → alerta actual sin formulario; `active` → alerta "Suscripción activa hasta {end_date}; la nueva solicitud se procesará junto a la vigente" + formulario + "Solicitar de nuevo"; else → actual ("Aceptar").
- Listado: resolver por servicio prioridad `requested/pending` > `paid` activa > ninguna (el dict actual muestra la última fila, erróneo tras re-solicitar).
- `commercial_public.html`: `requested` → ribbon "Solicitado" sin botón; `pending` → QR/"Ver factura"; `paid` activa → ribbon "Activo" + "Solicitar de nuevo"; else → "Solicitar".

## Áreas afectadas

| Área | Impacto |
|---|---|
| `apps/home/views/servicios/comerciales/views.py` | Modificado |
| `apps/home/templates/pages/home/services/service_detail.html` | Modificado |
| `apps/home/templates/pages/home/services/commercial_public.html` | Modificado |
| `apps/home/tests/test_services_ui.py` | Modificado |
| `apps/commercial/tests/test_views.py` | Modificado |

## Riesgos

| Riesgo | Prob. | Mitigación |
|---|---|---|
| Facturación doble por solapamiento | Media | El staff factura la fila nueva como hoy |
| Ambigüedad UI "tengo" vs. "quiero otra" | Media | Alerta + label "Solicitar de nuevo" |
| Dict `user_subscriptions` con fila errónea | Media | Resolver fila de decisión en la vista |

## Plan de reversión

Revertir el commit: restaura el bloqueo por no-expirado y las plantillas originales. Sin migraciones ni filas mutadas (solo se crean filas nuevas).

## Dependencias

Ninguna externa.

## Criterios de aceptación

- [ ] POST con `paid` activa crea fila `requested` nueva; la `paid` queda intacta.
- [ ] POST con `requested`/`pending` existente se bloquea con el mensaje actual, sin crear fila.
- [ ] Detalle: sin formulario ni botón con `requested`/`pending`; alerta info + formulario + "Solicitar de nuevo" con `paid` activa.
- [ ] Listado: ribbon "Activo" + "Solicitar de nuevo" con `paid` activa; sin botón con `requested`/`pending`.
- [ ] Tests nuevos en `test_services_ui.py` y `test_views.py`; suite completa verde; `manage.py check` y djlint OK.
