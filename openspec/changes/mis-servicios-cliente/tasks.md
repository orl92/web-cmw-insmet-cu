# Tasks: Mis Servicios del cliente y limpieza del catálogo comercial

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 430–460 |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | `format_cup` filter + all template usages + admin RISK-1 fix | PR 1 | `python manage.py test apps.commercial` | `python manage.py check` | `utils_filters.py`, admin `list.html`, `test_views.py` assertion |
| 2 | Catalog cleanup + Mis Servicios view + detail icons | PR 2 | `python manage.py test apps.home` | `python manage.py check` | `views.py`, `commercial_public.html`, `commercial.html`, `service_detail.html` |
| 3 | Menu visibility + counter bug fix | PR 3 | `python manage.py test apps.core` | `python manage.py check` | `context_processors.py`, `menu-list.html` |
| 4 | Full test suite + djlint | PR 4 | `python manage.py test` | `djlint --lint` | test files only |

## Phase 1: Price Helper (format_cup)

- [x] 1.1 Add `format_cup` filter to `apps/core/templatetags/utils_filters.py`: receives `Decimal|float|None`, returns `str` with `$` prefix, thousand separator `.`, decimal `,` (e.g. `$1.234,56`). Register as `@register.filter(name='format_cup')`.
- [x] 1.2 **RISK-1 RESOLUTION**: Apply `format_cup` in admin template `apps/commercial/templates/pages/commercial/service/list.html:19` — replace `${{ object.price|floatformat:2 }}` with `${{ object.price|format_cup }}`.
- [x] 1.3 Update admin assertion in `apps/commercial/tests/test_views.py:682`: change `assertIn('$45.50', html)` to `assertIn('$45,50', html)` (format_cup uses comma for decimals).
- [x] 1.4 Verify: `python manage.py test apps.commercial` green; `python manage.py check` passes.

## Phase 2: Views + Context Processor

- [x] 2.1 Modify `CommercialServicesListView.get_queryset` in `apps/home/views/servicios/comerciales/views.py`: remove `payment_status='paid', end_date__gt=ahora` filter. Add `Case(When)` ordering: requested=0, pending=1, paid=2, default=3, then `-start_date`.
- [x] 2.2 Add `STATUS_RIBBONS` dict and inject `status_ribbon` in `CommercialServicesListView.get_context_data`.
- [x] 2.3 Modify `PublicCommercialServicesListView.get_context_data`: remove `user_subscriptions` and `now` from context (keep `title`, `parent`, `segment`).
- [x] 2.4 Fix `client_pending_actions` bug in `apps/core/context_processors.py:75–82`: compute `client_pending_actions = client_requested_count + client_pending_count` in the normal path (after both queries), not only in the `except`.
- [x] 2.5 Modify `ServiceDetailView.get_context_data`: replace `price_per_period` with raw `format_cup`-ready `price` for template use; keep `billing_period` and `estimated_total`.

## Phase 3: Templates

- [ ] 3.1 Rewrite `apps/home/templates/pages/home/services/commercial.html`: dynamic ribbon via `status_ribbon|get_item:subscription.status_display`; contextual actions per state (activo → Ver PDF, pending+qr → Ver factura+Pagar QR, pending other → Ver factura, requested → "En proceso", expired → Solicitar); calendar icon before date range; `format_cup` for price.
- [ ] 3.2 Rewrite `apps/home/templates/pages/home/services/commercial_public.html`: remove ribbon blocks (lines 20–32) and per-state button blocks (lines 58–91); add `service.get_service_category_display` badge, `service.code` if exists, `format_cup` for price, single button: "Solicitar" (logged in) / "Iniciar sesión" with `ti ti-login`. Add `{% load my_filters %}` to `commercial.html` for `format_cup`.
- [ ] 3.3 Update `apps/home/templates/pages/home/services/service_detail.html`: unify submit to "Solicitar" + `ti ti-send` (line 157), Cancelar with `ti ti-x`, related "Ver" with `ti ti-eye`, price with `format_cup`.
- [ ] 3.4 Update `templates/includes/home/menu-list.html:159`: change `client_active_count > 0` to `client_active_count > 0 or client_expired_count > 0 or client_requested_count > 0 or client_pending_count > 0`; add badge `client_pending_actions` (requested+pending) on "Mis Servicios" link.
- [ ] 3.5 Verify: `python manage.py check` and `python manage.py test apps.home apps.core` green.

## Phase 4: Tests

- [ ] 4.1 Add unit tests for `format_cup` filter in `apps/core/tests/test_templatetags.py` (or create): Decimal, float, None, large number (thousand separator), zero.
- [ ] 4.2 Update `ServiceReRequestUiTests.test_public_list_active_shows_re_request_button` in `apps/home/tests/test_services_ui.py`: remove `assertIn('Activo', html)` and `assertIn('Solicitar de nuevo', html)` — catalog now shows single "Solicitar" button without state ribbon.
- [ ] 4.3 Update `ServiceReRequestUiTests.test_public_list_requested_shows_no_button`: remove `assertIn('Solicitado', html)` — no ribbon in catalog.
- [ ] 4.4 Update `ServiceReRequestUiTests.test_public_list_deterministic_precedence`: remove ribbon/button assertions; verify catalog renders with single "Solicitar" regardless of state.
- [ ] 4.5 Update `ServiceReRequestUiTests.test_active_paid_renders_form_and_cta`: change `assertIn('Solicitar de nuevo', html)` to `assertIn('Solicitar', html)`.
- [ ] 4.6 Verify `ServicesCommercialStaffButtonTests.test_pending_non_qr_shows_invoice_guidance` still passes (button moves to "Mis Servicios" — test should reference `home:services_commercial` if relocated, or confirm it still passes on public view if the button remains there).
- [ ] 4.7 Add test: `CommercialServicesListView` shows ALL subscription states (requested, pending, paid, expired) — not just paid active.
- [ ] 4.8 Add test: `client_pending_actions` computed in normal path (no exception) — mock request with requested+pending subs, verify context variable via `menu_notifications`.
- [ ] 4.9 Add test: menu "Mis Servicios" visible with any subscription state (requested/pending/paid/expired), not only active.
- [ ] 4.10 Run full suite: `python manage.py test`; verify `djlint . --lint` clean on modified templates.

## RISK-1 Resolution Summary

**Decision**: Apply `format_cup` to admin template `list.html:19` and update the `$45.50` assertion to `$45,50`.

**Rationale**: The design declares `format_cup` as the unique price helper across the project. Leaving the admin template with `floatformat:2` creates two rendering paths for the same data (`$45.50` vs `$45,50`), which is exactly the inconsistency this change aims to eliminate. Updating one line in the admin template and one test assertion is minimal cost for full coherence.

**Affected files**:
- `apps/commercial/templates/pages/commercial/service/list.html:19` — `floatformat:2` → `format_cup`
- `apps/commercial/tests/test_views.py:682` — `$45.50` → `$45,50`
