# Tasks: Reesolicitar servicio con suscripción activa

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 180–250 |
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
| 1 | All changes in one PR | PR 1 | `python manage.py test apps.home apps.commercial` | `python manage.py runserver` → visit service detail and public list as client | `apps/home/views/servicios/comerciales/views.py` + both templates |

## Phase 1: View Logic — ServiceDetailView

- [x] 1.1 In `apps/home/views/servicios/comerciales/views.py`, replace `existing_subscription` guard in `get_context_data` (line 100–105): query `in_flight` (`payment_status__in=['requested','pending']`) and `active` (`payment_status='paid', end_date__gt=timezone.now()`); set `context['in_flight_subscription']` and `context['active_subscription']`; remove `existing_subscription` key.
- [x] 1.2 In `ServiceDetailView.form_valid` (line 122–133), change filter from `.exclude(payment_status='expired')` to `.filter(payment_status__in=['requested', 'pending'])` so active paid rows no longer block re-request.
- [x] 1.3 In `PublicCommercialServicesListView.get_context_data` (line 58–60), replace dict comprehension with per-service deterministic resolver: precedence `requested/pending` (in-flight) > `paid` active (`end_date > now`) > last row. Keep `user_subscriptions[service.id]` as the resolved row.

## Phase 2: Template Branches — Detail + Public List

- [x] 2.1 In `apps/home/templates/pages/home/services/service_detail.html`, replace the single `{% if existing_subscription %}` block (line 55–67) with three branches: `{% if in_flight_subscription %}` → alert (no form, no button); `{% elif active_subscription %}` → info alert "Suscripción activa hasta {{ active_subscription.end_date }}; la nueva solicitud se procesará junto a la vigente" + form + CTA "Solicitar de nuevo"; `{% else %}` → default form (current behavior). Use djlint-compatible 2-space formatting.
- [x] 2.2 Update `service_detail.html` card-footer (line 148–161): show submit button only when `not in_flight_subscription` (both active and no-sub cases); label "Solicitar de nuevo" when `active_subscription`, "Aceptar" otherwise. Remove references to `existing_subscription`.
- [x] 2.3 In `apps/home/templates/pages/home/services/commercial_public.html`, update ribbon block (line 20–31): keep existing branches for requested/pending/paid; no change needed (already correct). Update button block (line 58–87): `paid` active → button "Solicitar de nuevo" linking to detail; `requested` → no button (keep ribbon); `pending` → "Ver factura" (existing); expired/none → "Solicitar" (existing). Remove the `<!-- No mostrar botón, ya tiene ribbon -->` comment for paid-active and replace with the new button.

## Phase 3: Tests — Commercial form_valid

- [x] 3.1 In `apps/commercial/tests/test_views.py`, add class `ServiceReRequestTests` with: `test_form_valid_with_active_paid_creates_requested_row` — create `paid` sub with future `end_date`, POST detail form, assert new `requested` row exists AND old `paid` row unchanged (`payment_status`, `end_date`).
- [x] 3.2 Add `test_form_valid_blocked_with_requested_sub` — create `requested` sub, POST, assert row count unchanged and warning message rendered.
- [x] 3.3 Add `test_form_valid_blocked_with_pending_sub` — create `pending` sub, POST, assert row count unchanged and warning message rendered.

## Phase 4: Tests — Home UI (detail + public list)

- [x] 4.1 In `apps/home/tests/test_services_ui.py`, add class `ServiceReRequestUiTests` with: `test_active_paid_renders_form_and_cta` — active paid sub → assert form present, button "Solicitar de nuevo", info alert with "activa hasta", no "Ya tienes" block.
- [x] 4.2 Add `test_in_flight_hides_form_and_button` — requested sub → assert form absent, submit button absent, alert rendered.
- [x] 4.3 Add `test_in_flight_pending_hides_form` — pending sub → assert form absent.
- [x] 4.4 Add `test_public_list_active_shows_re_request_button` — active paid sub → ribbon "Activo", button text "Solicitar de nuevo".
- [x] 4.5 Add `test_public_list_requested_shows_no_button` — requested sub → ribbon "Solicitado", no request button rendered.
- [x] 4.6 Add `test_public_list_deterministic_precedence` — create both `paid` active and `requested` rows for same service → assert resolved status is `requested` (in-flight wins), no request button.

## Phase 5: Verification

- [x] 5.1 Run `python manage.py check` — zero errors.
- [x] 5.2 Run `python manage.py test apps.home apps.commercial` — all tests green.
- [x] 5.3 Run `djlint --reformat --check --lint apps/home/templates/pages/home/services/service_detail.html apps/home/templates/pages/home/services/commercial_public.html` — clean.
- [x] 5.4 Run `ruff check apps/home/views/servicios/comerciales/views.py apps/home/tests/test_services_ui.py apps/commercial/tests/test_views.py` — clean.
- [x] 5.5 Verify `git diff --stat` shows only the 5 expected files; no migration files.
