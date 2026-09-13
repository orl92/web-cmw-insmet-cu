# Proposal: Pulido UI Servicios

## Intent

Feedback post-archivado de `mis-servicios-cliente`: el menú usa dot animado en vez del patrón badge de Avisos, los badges por estado viven en el ítem equivocado, la card de "Mis Servicios" tiene iconos de pago genéricos y precio con `ti-currency-dollar` redundante, el botón "Ver factura" produce 403 para clientes, y las páginas de error 400/403/404/500 no permiten volver atrás.

## Alcance

**Dentro (6 frentes):**
1. Menú: migrar badges de estado de "Servicios Comerciales" a "Mis Servicios"
2. Menú: reemplazar dot animado del toggle padre "Servicios" por badge `bg-red-lt` estilo Avisos
3. Card Mis Servicios: iconos de pago diferenciados, quitar `ti-currency-dollar`, layout metadata uniforme
4. Fix 403 "Ver factura": apuntar a `commercial:factura_download` con UUID + `?inline=1`
5. Páginas de error 400/403/404/500: botón "Volver" con fallback `history.back()`
6. Card catálogo público: quitar `ti-currency-dollar`, quitar bloque "Código:", badge categoría diferenciada

**Fuera:** `maintenance.html` (su botón es "Iniciar sesión"), cambios de modelo/migraciones, nuevo flujo de pago, refactor de context processor.

## Capacidades

### Nuevas
Ninguna.

### Modificadas
- `customer-menu-notifications`: badge padre "Servicios" reemplaza dot animado por `bg-red-lt` estilo Avisos; badges `requested`/`pending` migran de "Servicios Comerciales" a "Mis Servicios"
- `customer-services-dashboard`: botón "Ver factura" apunta a `commercial:factura_download/<uuid>?inline=1` (condicional a `invoices.exists()`); iconos de pago diferenciados (`ti-qrcode`/`ti-building-bank`/`ti-building-store`); quitar `ti-currency-dollar` del precio; layout metadata uniforme (fechas → pago → precio)
- `home-public-services-layout`: quitar `ti-currency-dollar` del precio; quitar bloque "Código:" con `ti-hash`; badge categoría diferenciada por icono (`ti-cloud` pronóstico, `ti-plant` agrometeo)

## Enfoque

**Hallazgos de exploración:**
- `format_cup` **SÍ antepone `$`** (`utils_filters.py` L19: `f"${format(value, ',.2f').translate(_ES_MX_TRANS)}"`) → icono `ti-currency-dollar` es redundante en ambos templates
- `factura_download` existe en `commercial:urls.py` L164 con `uuid` param; `InvoicePDFDownloadView.get_permission_required` ya permite owner access (test `InvoicePDFOwnerAccessTests` confirma)
- Patrón badge Avisos: `templates/includes/home/menu-list.html` L56-60 (`{% with total=... %}{% if total > 0 %}<span class="badge bg-red-lt ms-2">{{ total }}</span>{% endif %}{% endwith %}`)
- Dot actual: `menu-list.html` L133-135 (`status-dot status-dot-animated bg-red`)
- Error pages: 4 archivos idénticos (`400.html`, `403.html`, `404.html`, `500.html`) con `<a href="{% url 'home:index' %}">`
- Tests a actualizar: `test_menu_dot_animated_*` L744-761, `test_pending_qr_offers_*` L331-345, `test_requested_shows_*` L347-354

**Implementación:**
1. `menu-list.html`: quitar dot L133-135, agregar badge `bg-red-lt` estilo Avisos; quitar badges de "Servicios Comerciales" L149-156, agregarlos a "Mis Servicios" L165-171
2. `commercial.html`: condicionar `?inline=1` y UUID en "Ver factura" L69-72; reemplazar `ti-credit-card` por icono diferenciado según `payment_method` L36-41; quitar `ti-currency-dollar` L42-47
3. `commercial_public.html`: quitar `ti-currency-dollar` L32-35; quitar bloque código L36-41; badge categoría con icono diferenciado L28
4. `400.html`, `403.html`, `404.html`, `500.html`: reemplazar href con `onclick="if(window.history.length>1){event.preventDefault();history.back()}"`
5. Tests: actualizar aserciones en 5 métodos

## Áreas afectadas

| Área | Impacto |
|---|---|
| `templates/includes/home/menu-list.html` | Modificado — badges migran, dot → badge |
| `apps/home/templates/pages/home/services/commercial.html` | Modificado — fix factura, iconos, quitar dollar |
| `apps/home/templates/pages/home/services/commercial_public.html` | Modificado — quitar dollar, código, badge icono |
| `templates/layouts/400.html` | Modificado — history.back() |
| `templates/layouts/403.html` | Modificado — history.back() |
| `templates/layouts/404.html` | Modificado — history.back() |
| `templates/layouts/500.html` | Modificado — history.back() |
| `apps/home/tests/test_services_ui.py` | Modificado — 5 métodos de aserción |

## Riesgos

| Riesgo | Prob. | Mitigación |
|---|---|---|
| Template roto por cambio de patrón en menú | Baja | Seguir patrón exacto de Avisos L56-60; test `test_menu_dot_animated_*` |
| `format_cup` no antepone `$` (verificación) | Baja | Confirmado: `utils_filters.py` L19 sí antepone `$` |
| Botón "Ver factura" 403 si owner access falla | Baja | `InvoicePDFDownloadView` ya tiene owner access; test `InvoicePDFOwnerAccessTests` confirma |
| `history.back()` en error pages no tiene página previa | Baja | Guarda `window.history.length > 1` antes de `preventDefault()` |
| Tests fallan por cambio de URL en "Ver factura" | Media | Actualizar `assertIn(reverse('commercial:factura_list'))` a `factura_download` con UUID |

## Plan de reversión

Revert de los commits del cambio. Sin migraciones ni mutación de datos (solo templates y tests).

## Dependencias

- `mis-servicios-cliente` (archivado): este cambio refina su UI.
- Ninguna externa.

## Criterios de aceptación

- [ ] **Frente 1 (menú badges):** "Servicios Comerciales" no tiene badges; "Mis Servicios" tiene badge `bg-blue-lt` para `requested` y `bg-orange-lt` para `pending`
- [ ] **Frente 2 (badge padre):** Toggle "Servicios" muestra `<span class="badge bg-red-lt ms-2">{{ total }}</span>` cuando `client_pending_actions > 0`; sin dot animado
- [ ] **Frente 3 (card Mis Servicios):** Icono de pago diferenciado (`ti-qrcode`/`ti-building-bank`/`ti-building-store`); sin `ti-currency-dollar`; precio muestra `$` solo por `format_cup`; layout uniforme: fechas → pago → precio
- [ ] **Frente 4 (fix factura):** Botón "Ver factura" apunta a `commercial:factura_download/<uuid>?inline=1`; solo visible si `subscription.invoices.exists()`; sin 403
- [ ] **Frente 5 (error pages):** 400/403/404/500 tienen botón con `history.back()` + fallback `home:index`
- [ ] **Frente 6 (catálogo público):** Sin `ti-currency-dollar`; sin bloque "Código:"; badge categoría con icono diferenciado
- [ ] Tests actualizados: `test_menu_dot_animated_*`, `test_pending_qr_offers_*`, `test_pending_transfer_offers_*`, `test_requested_shows_*` pasan
- [ ] `python manage.py check`, suite completa verde, `djlint` OK
