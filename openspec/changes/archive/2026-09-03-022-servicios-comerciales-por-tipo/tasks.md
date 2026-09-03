# Tasks: Servicios Comerciales por Tipo (Categoría de Facturación)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 180–220 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

## Phase 1: Models — Service + ServiceSubscription

- [x] 1.1 `apps/commercial/models.py` — Add `service_category` CharField to `Service` (choices `agrometeo`/`pronostico`, default `pronostico`), after `price` field
- [x] 1.2 `apps/commercial/models.py` — Change `Service.PERIOD_DAYS = 30` → `PERIOD_DAYS = 1`; add `PERIOD_MONTHS = 1` constant
- [x] 1.3 `apps/commercial/models.py` — Add `Service.compute_end_date(start_date, quantity, category)` static method: `relativedelta(months=quantity)` for agrometeo, `timedelta(days=quantity)` for pronostico. Import `from dateutil.relativedelta import relativedelta`
- [x] 1.4 `apps/commercial/models.py` — Add `get_billing_period_display()` and `get_price_per_period_display()` methods to `Service`
- [x] 1.5 `apps/commercial/models.py` — Add `quantity` PositiveIntegerField (default=1, `MinValueValidator(1)`) to `ServiceSubscription`
- [x] 1.6 `apps/commercial/models.py` — Add `start_date >= end_date` validation to `ServiceSubscription.clean()`

## Phase 2: Forms — PaymentMethodForm

- [x] 2.1 `apps/commercial/forms/subscription.py` — Replace `end_date` field with `quantity = forms.IntegerField(min_value=1, label='Cantidad')` in `PaymentMethodForm`
- [x] 2.2 `apps/commercial/forms/subscription.py` — Add `from dateutil.relativedelta import relativedelta` import

## Phase 3: Views — Permission Fix + Invoice Logic

- [x] 3.1 `apps/commercial/views/invoices.py:445` — Fix `@permission_required('commercial.view_servicesubscription')` → `'commercial.view_subscription'`
- [x] 3.2 `apps/commercial/views/invoices.py` — In `ajax_pending_subscriptions`: add `data-quantity="{sub.quantity}"` to checkbox HTML
- [x] 3.3 `apps/commercial/views/invoices.py` — In `process_batch_invoice`: replace `days_count = (end_date - start_date).days` with `quantity = sub.quantity`; `amount = price * quantity`; set `unidad_medida='MES'` if agrometeo else `'DÍA'`
- [x] 3.4 `apps/commercial/views/invoices.py` — In `process_manual_invoice`: replace `days_count` with `quantity = 1` default; `importe = quantity * cd['precio']`; set `unidad_medida` by category

## Phase 4: Views — Subscription + Detail

- [x] 4.1 `apps/commercial/views/subscriptions.py` — In `SubscriptionRenewView.form_valid`: replace `timedelta(days=30)` with `Service.compute_end_date(now, old.quantity, old.service.service_category)`
- [x] 4.2 `apps/home/views/servicios/comerciales/views.py` — In `ServiceDetailView.get_context_data`: change `estimated_total = price * PERIOD_DAYS` → `price * 1`; add `billing_period = service.get_billing_period_display()` to context
- [x] 4.3 `apps/home/views/servicios/comerciales/views.py` — In `ServiceDetailView.form_valid`: replace `end_date = form.cleaned_data['end_date']` with `quantity = form.cleaned_data['quantity']`; compute `end_date = Service.compute_end_date(start_date, quantity, self.service.service_category)`; pass `quantity=quantity` to `ServiceSubscription`

## Phase 5: Templates

- [x] 5.1 `apps/home/templates/pages/home/services/service_detail.html` — Replace `Período estándar: {{ service.PERIOD_DAYS }} días` with `Período: {{ service.get_billing_period_display }}`
- [x] 5.2 `apps/home/templates/pages/home/services/service_detail.html` — Replace price line with `Precio por {{ service.get_billing_period_display }}: ${{ service.price|floatformat:2 }}`
- [x] 5.3 `apps/home/templates/pages/home/services/service_detail.html` — Replace `Monto estimado ({{ service.PERIOD_DAYS }} días)` with `Monto estimado (1 {{ billing_period }})`
- [x] 5.4 `apps/home/templates/pages/home/services/service_detail.html` — Replace `end_date` form field with `quantity` field; add `data-category` attr and JS for dynamic label ("cantidad de días" / "cantidad de meses")
- [x] 5.5 `apps/home/templates/pages/home/services/commercial_public.html` — Insert staff block after image: `{% if perms.commercial.change_service %}` Editar button + `{% if perms.commercial.add_service %}` Nuevo servicio link
- [x] 5.6 `apps/home/templates/pages/home/services/commercial_public.html` — In pending block (non-QR): add "Ver factura" link to `commercial:factura_list`

## Phase 6: Tests — Fix Existing + New

- [x] 6.1 `apps/commercial/tests/test_service_detail.py` — Change `assertEqual(Service.PERIOD_DAYS, 30)` → `assertEqual(Service.PERIOD_DAYS, 1)`
- [x] 6.2 `apps/commercial/tests/test_service_detail.py` — Update template assertions: replace "30 días" checks with `get_billing_period_display` output
- [x] 6.3 `apps/home/tests/test_services_ui.py` — Add `ServicesCommercialStaffButtonTests`: staff user sees Editar + Nuevo servicio buttons; anonymous does not
- [x] 6.4 `apps/commercial/tests/test_views.py` — Add test for `ajax_pending_subscriptions`: staff gets 200 (not 403), response includes `data-quantity`
- [x] 6.5 `apps/commercial/tests/test_views.py` — Add test for `process_batch_invoice`: `cantidad = quantity`, `importe = price × quantity`, `unidad_medida` by category
- [x] 6.6 `apps/commercial/tests/test_views.py` — Add test for `SubscriptionRenewView`: end_date computed via `compute_end_date` with correct quantity/category
- [x] 6.7 `apps/commercial/tests/test_service_detail.py` — Add test: `Service.compute_end_date(date(2026,1,31), 2, 'agrometeo')` → `date(2026,3,31)` (no overflow)
- [x] 6.8 `apps/commercial/tests/test_service_detail.py` — Add test: `Service.compute_end_date(date(2026,1,1), 5, 'pronostico')` → `date(2026,1,6)`

## Phase 7: Migration + Final Verification

- [x] 7.1 Run `python manage.py makemigrations commercial` — generates 2 migrations (service_category + quantity) with defaults
- [x] 7.2 Run `python manage.py check` — verify no system check errors
- [x] 7.3 Run `python manage.py test apps.commercial apps.home` — all tests pass
- [x] 7.4 Run `pre-commit run --all-files` — Ruff + djlint + detect-secrets clean
