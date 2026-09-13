# Diseño: Pulido UI Servicios

## Enfoque técnico

Refino de UI template-only (6 frentes, 8 archivos modificados, 0 nuevos). No hay migraciones, ni modelos, ni permisos nuevos. Cada frente se implementa y verifica independientemente.

## Decisiones de diseño

### 1. UUID de factura más reciente en template

| Opción | Tradeoff | Decisión |
|---|---|---|
| Query en template (`subscription.invoices.order_by('-issue_date').first.uuid`) | N+1 no visible en menu, pero sí en card × N subs | Descartada |
| Subquery `annotate` en queryset | Complicada con `Subquery` + `OuterRef`; precio por sheet | Descartada |
| Helper en `get_context_data` con loop sobre page | Simple, 1 query adicional, mantiene lógica en vista | **Elegida** |

**Implementación:** En `CommercialServicesListView.get_context_data`, iterar `subscriptions` y adjuntar `subscription._latest_invoice_uuid = sub.invoices.order_by('-issue_date').first()` (el objeto Invoice, no solo uuid — permite acceso a `uuid` en template sin query adicional). El template usa `{% with invoice=subscription._latest_invoice_uuid %}` y `commercial:factura_download/{{ invoice.uuid }}?inline=1`.

### 2. Método de pago a icono

| Opción | Tradeoff | Decisión |
|---|---|---|
| Filtro template `payment_method_icon` | Reutilizable, testeable unitariamente, separación de responsabilidades | **Elegida** |
| `{% if %}` chain en template | Repetible en otros templates, harder de testear | Descartada |

**Implementación:** Nuevo filtro en `utils_filters.py`: `payment_method_icon`. Mapeo: `qr` → `ti-qrcode`, `transfer` → `ti-building-bank`, `presencial` → `ti-building-store`, default → `ti-credit-card`. Retorna string con clase CSS.

### 3. Layout metadata uniforme

**Orden fijo en DOM** (sin dependencia de flex-wrap):
1. Fechas: `<span><i class="icon ti ti-calendar-month"></i> dd/mm/yyyy - dd/mm/yyyy</span>`
2. Pago: `<span><i class="icon ti {{ payment_method|payment_method_icon }}"></i> display</span>`
3. Precio: `<span>{{ price|format_cup }} CUP/periodo</span>` (sin `ti-currency-dollar`)

Cada `<span>` es un hijo directo de `.d-flex.flex-wrap.gap-2`. El orden en el DOM determina el visual; `flex-wrap` solo gestiona responsive.

### 4. Badges menú — patrón Avisos

Reutilizar exactamente el patrón de `menu-list.html` L56-60:

- **Padre "Servicios"**: `{% if client_pending_actions > 0 %}<span class="badge bg-red-lt ms-2">{{ client_pending_actions }}</span>{% endif %}` — reemplaza dot animado.
- **Hijo "Mis Servicios"**: badges `bg-blue-lt` (requested) + `bg-orange-lt` (pending) — se migran desde "Servicios Comerciales" (L149-156).
- **"Servicios Comerciales"**: se eliminan los badges de estado (solo queda el label).

## Flujo de datos

    Context Processor → menu-list.html (padre badge bg-red-lt)
         │
         ├── client_pending_actions (requested + pending)
         ├── client_requested_count → badge bg-blue-lt en "Mis Servicios"
         └── client_pending_count  → badge bg-orange-lt en "Mis Servicios"

    CommercialServicesListView.get_context_data
         │
         └── subscription._latest_invoice_uuid → commercial.html (botón Ver factura)

## Cambios por archivo

| Archivo | Acción | Cambios |
|---|---|---|
| `templates/includes/home/menu-list.html` | Modificar | L133-135: dot animado → badge `bg-red-lt`. L149-156: eliminar badges de "Servicios Comerciales". L165-171: migrar badges requested/pending a "Mis Servicios" |
| `apps/home/templates/pages/home/services/commercial.html` | Modificar | L38: `ti-credit-card` → `payment_method_icon` filter. L42-47: quitar `ti-currency-dollar`. L69-72: `factura_list` → `factura_download/<uuid>?inline=1` condicional. Layout uniforme |
| `apps/home/templates/pages/home/services/commercial_public.html` | Modificar | L32-35: quitar `ti-currency-dollar`. L36-41: eliminar bloque código. L28: badge categoría con icono (`ti-cloud`/`ti-plant`) |
| `templates/layouts/400.html` | Modificar | L20-23: añadir `onclick` history.back() + href fallback |
| `templates/layouts/403.html` | Modificar | L20-23: misma modificación |
| `templates/layouts/404.html` | Modificar | L20-23: misma modificación |
| `templates/layouts/500.html` | Modificar | L20-23: misma modificación |
| `apps/home/views/servicios/comerciales/views.py` | Modificar | `get_context_data`: añadir `_latest_invoice_uuid` por subscription |
| `apps/core/templatetags/utils_filters.py` | Modificar | Nuevo filtro `payment_method_icon` |
| `apps/home/tests/test_services_ui.py` | Modificar | 5 métodos: actualizar aserciones |

## Estrategia de tests

| Método | Cambio de aserción |
|---|---|
| `test_menu_dot_animated_shown_when_pending_actions` (L744) | `status-dot` → `badge bg-red-lt` con "2" en toggle padre; badge `bg-blue-lt` + `bg-orange-lt` en "Mis Servicios" |
| `test_menu_dot_animated_hidden_without_pending_actions` (L754) | Verificar ausencia de badge `bg-red-lt` en toggle padre |
| `test_pending_qr_offers_invoice_and_qr_payment` (L331) | `factura_list` → `factura_download/<uuid>?inline=1`; verificar icono `ti-qrcode` |
| `test_pending_transfer_offers_invoice_without_qr` (L339) | `factura_list` → `factura_download/<uuid>?inline=1`; verificar icono `ti-building-bank` |
| `test_requested_shows_progress_badge_without_action_buttons` (L347) | Sin cambios (ya pasa) |

**Tests nuevos** (en `CommercialCatalogCodeAndCategoryUITests` o clase dedicada):
- `test_catalog_category_badge_has_cloud_icon`: categoría pronóstico → `ti-cloud`
- `test_catalog_category_badge_has_plant_icon`: categoría agrometeo → `ti-plant`
- `test_catalog_no_currency_dollar_icon`: ausencia de `ti-currency-dollar`
- `test_catalog_no_code_block`: ausencia de `Código:`
- `test_subscription_payment_icon_qr`: pending+qr → `ti-qrcode` en card
- `test_subscription_payment_icon_transfer`: pending+transfer → `ti-building-bank`
- `test_subscription_no_dollar_icon_in_price`: ausencia de `ti-currency-dollar` en card
- `test_error_pages_history_back`: 400/403/404/500 → `history.back()` presente

## Verificación

```bash
python manage.py check
python manage.py test apps.home apps.commercial
djlint . --reformat --check
djlint . --lint
```

## Amenaza y seguridad

N/A — sin routing, shell, subprocess, VCS/PR automation, executable-file classification, ni process-integration boundary.

## Migración / despliegue

Sin migración. Solo templates, 1 filtro y 1 vista context. Deploy estándar: `collectstatic --link --no-input`.

## Riesgos y mitigaciones

| Riesgo | Prob. | Mitigación |
|---|---|---|
| N+1 queries por `_latest_invoice_uuid` | Baja | Query ligera (1 por sub, `order_by` + `first`); subs por página ≤ 10 |
| Template roto por cambio de patrón badges menú | Baja | Seguir patrón exacto de Avisos; tests existentes + nuevos |
| `history.back()` sin historial previo | Baja | Guard `window.history.length > 1` antes de `preventDefault()` |
| Tests pendientes no pasan por falta de invoice | Media | Tests de "Ver factura" crean `Invoice` asociada al sub en setUp |

## Preguntas abiertas

Ninguna — todo está determinado por proposal + specs existentes.
