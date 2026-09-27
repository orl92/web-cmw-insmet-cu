# Tasks: Layout Cards Servicios

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 150–180 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto-chain |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Templates + tests | PR 1 | `python manage.py test apps.home` | `python manage.py check` | `commercial_public.html`, `commercial.html`, `test_services_ui.py` |

## Phase 1: Template Catálogo Público

- [x] 1.1 `apps/home/templates/pages/home/services/commercial_public.html` L30-41: reemplazar `<span class="d-flex flex-wrap gap-2 text-secondary mt-auto mb-3">` + `<div class="d-flex flex-wrap gap-2 mt-auto mb-3">` por wrapper `<div class="d-flex flex-column flex-grow-1 text-secondary mb-3">` con 3 `<div class="mb-2">`: Categoría (icono `ti-cloud`/`ti-plant` me-1 + "Categoría:" `<strong>{{ service.get_service_category_display }}</strong>`); Período (`ti-calendar-event` me-1 + "Período:" `<strong>{{ service.get_billing_period_display }}</strong>`); Precio `<span class="display-6 fw-bold text-primary">{{ service.price|format_cup|default_if_none:'—' }} <small class="text-secondary">CUP/{{ service.get_billing_period_display }}</small></span>`. L43 acciones conserva su `mt-auto` (redundante D1). `python manage.py test apps.home.tests.test_services_ui.CommercialCatalogCodeAndCategoryUITests`.

## Phase 2: Template Mis Servicios

- [x] 2.1 `apps/home/templates/pages/home/services/commercial.html` L31-45: reemplazar `<div class="d-flex flex-wrap gap-2 text-secondary mt-auto mb-3">` por wrapper `<div class="d-flex flex-column flex-grow-1 text-secondary mb-3">` (D1) con `<div class="mb-2">` por línea: Fechas `ti-calendar-month` me-1 (corrige baseline rojo L33 `ti-calendar`) + rango `d/m/Y`; Pago condicional (`if payment_method`) `payment_method_icon` me-1 + display; Categoría `ti-tag` me-1 + "Categoría:" `<strong>get_service_category_display</strong>`; Período `ti-calendar-event` me-1 + "Período:" `<strong>get_billing_period_display</strong>`; Precio condicional (`service_type == 'commercial'`) `<span class="display-6 fw-bold text-primary">{{ subscription.service.price|format_cup }}</span>` SOLO monto. `python manage.py test apps.home.tests.test_services_ui.CommercialServicesListViewStateScopeTests`.

- [x] 2.2 `apps/home/templates/pages/home/services/commercial.html` tras 2.1: `grep -c 'mt-auto'` → 0 (pin vía wrapper `flex-grow-1`; sin `mt-auto` en acciones).

## Phase 3: Tests — Baseline + Actualizar

- [x] 3.1 `apps/home/tests/test_services_ui.py` `test_metadata_layout_order_is_dates_payment_price` L315-331: marcador → `d-flex flex-column flex-grow-1 text-secondary mb-3`; marcador precio `CUP/` → output `format_cup` (`$`); orden fechas → pago (`ti-building-bank`) → categoría (`ti-tag`) → período (`ti-calendar-event`) → precio.

- [x] 3.2 `apps/home/tests/test_services_ui.py` `test_catalog_category_badge_has_cloud_icon` L568-579 y `_plant_icon` L581-592: asertar `ti-cloud`/`ti-plant` con `me-1` ANTES de "Categoría:" en línea `<div class="mb-2">`.

- [x] 3.3 `apps/home/tests/test_services_ui.py`: NUEVO test `test_catalog_dom_order_category_period_price` — orden categ→período→precio en wrapper `d-flex flex-column flex-grow-1`, sin `d-flex flex-wrap gap-2`.

- [x] 3.4 `apps/home/tests/test_services_ui.py`: NUEVO test `test_catalog_price_uses_display6_highlight` — `<span class="display-6 fw-bold text-primary">` con `format_cup` + `<small class="text-secondary">CUP/…</small>`.

## Phase 4: Tests — Nuevos Escenarios Mis Servicios

- [x] 4.1 `apps/home/tests/test_services_ui.py`: NUEVO test `test_subscription_lines_have_strong` — `<strong>` en líneas categoría y período.

- [x] 4.2 `apps/home/tests/test_services_ui.py`: NUEVO test `test_subscription_payment_icon_presencial` — `presencial` → `ti-building-store` me-1 antes del texto.

- [x] 4.3 `apps/home/tests/test_services_ui.py`: NUEVO test `test_subscription_no_payment_method_omits_line` — sin `payment_method` → ausencia de línea pago.

- [x] 4.4 `apps/home/tests/test_services_ui.py`: NUEVO test `test_subscription_commercial_only_price_highlight` — `service_type=PUBLIC` → sin `display-6`, con fechas + período.

- [x] 4.5 `apps/home/tests/test_services_ui.py`: NUEVO `test_subscription_price_no_suffix` — `display-6` con `format_cup` SIN `CUP/` (período en línea propia).

## Phase 5: Verificación

- [x] 5.1 `python manage.py check && python manage.py test apps.home --parallel` → 0 failures; baseline rojo (`test_calendar_icon_precedes_date_range_in_dom`, `test_metadata_layout_order_is_dates_payment_price`) verde.

- [x] 5.2 `djlint apps/home/templates/pages/home/services/commercial_public.html apps/home/templates/pages/home/services/commercial.html --reformat --check && djlint (ambos) --lint` → 0 errores.
