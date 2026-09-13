# Tasks: Pulido UI Servicios

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 100–150 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: stacked-to-main
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Filtro templatetag + contexto vista + templates menú/card + error pages + tests | PR 1 | `python manage.py test apps.home apps.core` | `python manage.py check` | `utils_filters.py`, `views.py`, `menu-list.html`, `commercial.html`, `commercial_public.html`, error layouts, `test_services_ui.py` |

## Phase 1: Templatetag + Vista

- [x] 1.1 Añadir filtro `payment_method_icon` a `apps/core/templatetags/utils_filters.py`: mapea `qr` → `ti-qrcode`, `transfer` → `ti-building-bank`, `presencial` → `ti-building-store`, default → `ti-credit-card`. Retorna string con clase CSS. Registrar con `@register.filter(name='payment_method_icon')`.
- [x] 1.2 Modificar `CommercialServicesListView.get_context_data` en `apps/home/views/servicios/comerciales/views.py`: iterar `page_obj` y adjuntar `subscription.latest_invoice = sub.invoices.order_by('-issue_date').first()` por cada suscripción. Guard: `hasattr(sub, 'invoices')`.

## Phase 2: Templates Menú + Card

- [x] 2.1 `templates/includes/home/menu-list.html` L133-135: reemplazar dot animado (`status-dot status-dot-animated bg-red`) por badge `bg-red-lt` estilo Avisos (`<span class="badge bg-red-lt ms-2">{{ client_pending_actions }}</span>`).
- [x] 2.2 `templates/includes/home/menu-list.html` L149-156: eliminar badges `bg-blue-lt`/`bg-orange-lt` de "Servicios Comerciales".
- [x] 2.3 `templates/includes/home/menu-list.html` L165-171: migrar badges `bg-blue-lt` (requested) y `bg-orange-lt` (pending) a "Mis Servicios".
- [x] 2.4 `apps/home/templates/pages/home/services/commercial.html` L38: reemplazar `ti-credit-card` por `{{ subscription.payment_method|payment_method_icon }}`.
- [x] 2.5 `apps/home/templates/pages/home/services/commercial.html` L42-47: quitar `ti-currency-dollar` del bloque de precio (dejar solo `format_cup`).
- [x] 2.6 `apps/home/templates/pages/home/services/commercial.html` L69-72: condicionar botón "Ver factura" a `subscription.latest_invoice` y apuntar a `commercial:factura_download/{{ invoice.uuid }}?inline=1`.

## Phase 3: Catálogo Público + Error Pages

- [x] 3.1 `apps/home/templates/pages/home/services/commercial_public.html` L28: añadir icono diferenciado al badge categoría (`ti-cloud` pronóstico, `ti-plant` agrometeo).
- [x] 3.2 `apps/home/templates/pages/home/services/commercial_public.html` L32-35: quitar `ti-currency-dollar` del precio.
- [x] 3.3 `apps/home/templates/pages/home/services/commercial_public.html` L36-41: eliminar bloque "Código:".
- [x] 3.4 `templates/layouts/400.html` L20-23: añadir `onclick="if(window.history.length>1){event.preventDefault();history.back()}"` al `<a>`.
- [x] 3.5 `templates/layouts/403.html` L20-23: misma modificación que 3.4.
- [x] 3.6 `templates/layouts/404.html` L20-23: misma modificación que 3.4.
- [x] 3.7 `templates/layouts/500.html` L20-23: misma modificación que 3.4.

## Phase 4: Tests

- [x] 4.1 Actualizar `test_menu_dot_animated_shown_when_pending_actions` (L744): asertar badge `bg-red-lt` con "2" en toggle padre; badge `bg-blue-lt` + `bg-orange-lt` en "Mis Servicios".
- [x] 4.2 Actualizar `test_menu_dot_animated_hidden_without_pending_actions` (L754): verificar ausencia de badge `bg-red-lt` en toggle padre.
- [x] 4.3 Actualizar `test_pending_qr_offers_invoice_and_qr_payment` (L331): `factura_list` → `factura/<uuid>/pdf/?inline=1`; verificar icono `ti-qrcode`.
- [x] 4.4 Actualizar `test_pending_transfer_offers_invoice_without_qr` (L339): `factura_list` → `factura/<uuid>/pdf/?inline=1`; verificar icono `ti-building-bank`.
- [x] 4.5 Añadir tests nuevos: `test_catalog_category_badge_has_cloud_icon`, `test_catalog_no_currency_dollar_icon`, `test_catalog_no_code_block`, `test_subscription_payment_icon_qr`, `test_subscription_no_dollar_icon_in_price`, `test_error_pages_history_back`.

## Phase 5: Verificación Final

- [x] 5.1 Ejecutar `python manage.py check` y `python manage.py test apps.home apps.commercial`.
- [x] 5.2 Ejecutar `djlint . --reformat --check` y `djlint . --lint` sobre templates modificados.
- [x] 5.3 Verificar que `gentle-ai sdd-status pulido-ui-servicios --cwd . --json` reporta `tasks: present`.
