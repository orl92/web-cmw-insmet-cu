# Change Proposal: Mis Servicios del cliente y limpieza del catálogo comercial

## Why

- La lógica de estado (ribbons + acciones por estado) vive hoy en el catálogo público (`commercial_public.html`), pero pertenece al panel del cliente. "Mis Servicios" (`commercial.html`) oculta toda suscripción no `paid` activa y hardcodea el ribbon "Activo".
- Formato de precio inconsistente: 3 variantes (`floatformat:2` en templates, f-string en `get_price_per_period_display()`, sin separador de miles).
- Botones sin icono: "Pagar con QR", "Iniciar sesión", "Ver" (relacionado) y submits del detail.
- Bug: `client_pending_actions` solo se setea en el `except` de `menu_notifications()`, así que el dot animado del menú nunca aparece.

## What Changes

### Capacidades (contrato con sdd-spec)

- **Nueva** `customer-services-dashboard`: "Mis Servicios" lista TODAS las suscripciones del cliente con ribbon por `status_display` (activo/pendiente/solicitado/expirado), acciones contextuales por estado y metadatos normalizados (icono calendario ANTES del rango, precio con período, método de pago).
- **Nueva** `customer-menu-notifications`: badge "Mis Servicios" = `requested + pending` del cliente; `client_pending_actions` calculado en el path normal (dot animado funcional).
- **Modificada** `home-public-services-layout`: el card del catálogo comercial público deja de renderizar ribbons/botones por estado; queda imagen, título, badge de categoría, precio formateado, summary y botón único ("Solicitar" logueado / "Iniciar sesión" anónimo).
- **Modificada** `commercial-service-categories`: el card público expone el badge de categoría (agrometeo/pronóstico) y el código único de forma discreta (referencia en facturas).

### Cambios

1. **Card catálogo**: precio `$1.234,56 CUP/mes` (helper único con separador de miles + período, reutilizado en catálogo, Mis Servicios y detail), badge de categoría, código discreto.
2. **"Solicitar de nuevo" → "Solicitar"**: en catálogo y en el submit del detail (se unifica "Solicitar de nuevo/Aceptar"); se conserva la semántica de re-solicitud (fila `requested` junto a la vigente y alerta del detail) heredada de `reesolicitar-servicio-activo`.
3. **Iconos**: "Pagar con QR" → `ti ti-qrcode`; "Iniciar sesión" → `ti ti-login`; "Ver" → `ti ti-eye`; submit detail → `ti ti-send`; "Cancelar" → `ti ti-x`.
4. **Mis Servicios**: queryset sin filtro de estado (todos los `ServiceSubscription` del customer). Acciones: `paid` activa → Ver PDF certificado (modal); `pending`+qr → Ver factura + Pagar con QR; `pending` transfer/presencial → Ver factura; `requested` → "En proceso" sin botones; `expired` → "Solicitar" (renovar). Metadatos: calendario antes del rango, precio con período, método de pago.
5. **Catálogo limpio**: eliminar ribbons por estado, botones por estado e inyección de `user_subscriptions`/`now` en `PublicCommercialServicesListView`. El menú "Mis Servicios" se muestra con ≥1 suscripción (cualquier estado).
6. **Contador**: en `menu_notifications()`, `client_pending_actions = client_requested_count + client_pending_count` en el path normal; badge en `menu-list.html:166-167`.

## Impact

| Área | Impacto | Detalle |
|---|---|---|
| `apps/home/views/servicios/comerciales/views.py` | Modificado | `CommercialServicesListView` lista todos los estados; `PublicCommercialServicesListView` sin `user_subscriptions`/`now`; submit detail unificado |
| `apps/home/templates/pages/home/services/commercial.html` | Modificado | Ribbons dinámicos, acciones contextuales, metadatos y precio normalizados |
| `apps/home/templates/pages/home/services/commercial_public.html` | Modificado | Card limpio + iconos nuevos |
| `apps/home/templates/pages/home/services/service_detail.html` | Modificado | Submit "Solicitar" + `ti ti-send`, Cancelar `ti ti-x`, "Ver" `ti ti-eye` |
| `apps/core/context_processors.py` | Modificado | Fix `client_pending_actions` en path normal |
| `templates/includes/home/menu-list.html` | Modificado | Badge Mis Servicios = requested+pending; visibilidad con ≥1 suscripción |
| `apps/commercial/models.py` / `apps/core/templatetags/` | Modificado | Helper único de precio con separador de miles |
| Tests (`apps/home/tests/test_services_ui.py`, `apps/commercial/tests/test_views.py`) | Modificado | Estados, acciones, formatos, iconos |

## Criterios de Aceptación

- [ ] Mis Servicios lista todas las suscripciones; ribbon correcto por estado y acciones contextuales según la tabla del punto 4.
- [ ] Catálogo público sin ribbons/botones por estado; card con precio `$1.234,56 CUP/mes`, badge de categoría y botón único.
- [ ] Iconos correctos en todos los botones listados (`qrcode`, `login`, `eye`, `send`, `x`).
- [ ] Precio idéntico (mismo helper) en catálogo, Mis Servicios y detail.
- [ ] Icono de calendario antes del rango en Mis Servicios.
- [ ] Badge del menú muestra requested+pending; dot animado visible cuando `client_pending_actions > 0`.
- [ ] `python manage.py check`, suite completa verde, `djlint` OK.

## Riesgos

| Riesgo | Prob. | Mitigación |
|---|---|---|
| Conflicto con `reesolicitar-servicio-activo` (implementado, sin archivar): su alcance en el catálogo queda reemplazado | Media | Declarar supersedido al archivar; conservar la semántica in-flight en el detail |
| `PagoView` es genérica (sin contexto de suscripción/factura) | Media | Reutilizar `home:payment`; pasar uuid por query param solo si el diseño lo exige |
| Tests existentes asertan formatos de precio | Media | Actualizar aserciones al nuevo helper; correr suite completa |
| Dos specs de `commercial-service-categories` (022 y `categoria-y-layout-servicios`) | Baja | La fase spec verifica cuál es vigente antes del delta |

## Plan de Reversión

Revert de los commits del cambio (templates, views, context processor y filtro nuevo). Sin migraciones ni mutación de datos (cambios de display y consultas de lectura).

## Dependencias

- `reesolicitar-servicio-activo` (implementado): este cambio ajusta su UI, no su lógica.
- Ninguna externa.
