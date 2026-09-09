# Exploration: Reesolicitar servicio con suscripción activa

Change name: `reesolicitar-servicio-activo`

## Goal

Allow a client to request a commercial service *again* even while they already have it active (paid). Today any existing non-expired `ServiceSubscription` (requested/pending/paid) blocks a new request in the client portal.

## Current State

The client-facing request path lives in `apps/home/views/servicios/comerciales/views.py` (`ServiceDetailView`) and two templates. The blocking logic is duplicated across the view and both templates.

### Blocking points (quoted with line numbers)

1. `ServiceDetailView.form_valid` — blocks creation for any non-expired existing row:
   ```python
   # apps/home/views/servicios/comerciales/views.py:122-133
   def form_valid(self, form):
       customer = self.request.user.commercial_customer
       existing = (
           ServiceSubscription.objects.filter(customer=customer, service=self.service)
           .exclude(payment_status='expired')
           .first()
       )
       if existing:
           messages.warning(
               self.request, 'Ya tienes una solicitud o suscripción para este servicio.'
           )
           return redirect('home:services_commercial_detail', uuid=self.service.uuid)
   ```

2. `ServiceDetailView.get_context_data` — sets `existing_subscription` for any non-expired row, which drives hiding in the template:
   ```python
   # apps/home/views/servicios/comerciales/views.py:98-106
   if self.request.user.is_authenticated and hasattr(self.request.user, 'commercial_customer'):
       customer = self.request.user.commercial_customer
       existing = (
           ServiceSubscription.objects.filter(customer=customer, service=self.service)
           .exclude(payment_status='expired')
           .first()
       )
       context['existing_subscription'] = existing
   ```

3. `apps/home/templates/pages/home/services/service_detail.html`:
   - Lines 55-67: alert box rendered whenever `existing_subscription` is truthy (message keyed to `paid`+`is_active` / `pending` / `requested`).
   - Line 68: the request `<form>` is only rendered inside `{% else %}` (i.e. when `not existing_subscription`).
   - Lines 149-160: submit button only rendered when `user.commercial_customer and not existing_subscription`; otherwise only a Cancel link.

4. `apps/home/templates/pages/home/services/commercial_public.html` — lines 58-93: the "Solicitar" button is hidden whenever `user_subscriptions[service.id]` exists and is **not** expired:
   - `paid & end_date > now` → ribbon "Activo", no button (lines 62-64)
   - `pending` → "Pagar con QR" / "Ver factura" (lines 64-73)
   - `requested` → no button (lines 74-76)
   - `else` (expired or missing) → "Solicitar" (lines 76-87)

### Staff-side request path (NOT blocked)

`SubscriptionCreateView` (`apps/commercial/views/subscriptions.py:62-91`) is a plain `CreateView` with `permission_required = 'commercial.add_subscription'`. It has **no** blocking on existing subscriptions — staff can already create multiple rows per customer+service.

### Renewal precedent (multiple rows coexist)

`SubscriptionRenewView` (`apps/commercial/views/subscriptions.py:128-180`, URL `commercial:suscripcion_renew`, not reachable from any UI link) already creates a **new** `requested` subscription while the old paid one stays active:

```python
# apps/commercial/views/subscriptions.py:147-161
def form_valid(self, form):
    ...
    new_sub = ServiceSubscription.objects.create(
        customer=old.customer,
        service=service,
        start_date=start_date,
        end_date=end_date,
        quantity=new_quantity,
        payment_status='requested',
        record_active=True,
    )
```

The model has **no unique constraint** on `(customer, service)`. `ServiceSubscription.Meta` (`apps/commercial/models.py:213-222`) defines only custom permissions — no constraints. This is confirmed by the renew test at `apps/commercial/tests/test_views.py:1134-1183` (`SubscriptionRenewQuantityTests`), which creates a new `requested` sub while `old` is `paid`.

## Affected Areas

- `apps/home/views/servicios/comerciales/views.py` — `ServiceDetailView.get_context_data` (98-106) and `.form_valid` (122-133): the blocking logic to relax/remove.
- `apps/home/templates/pages/home/services/service_detail.html` — lines 55-67 (alert), 68-111 (form visibility), 149-160 (submit button).
- `apps/home/templates/pages/home/services/commercial_public.html` — lines 58-93 (Solicitar button visibility per status).
- `apps/home/tests/test_services_ui.py` — `ServicesPublicUiTests` (33), `ServicesCommercialUiTests` (102), `ServicesCommercialStaffButtonTests` (186), `ServicesVisibilityFilterTests` (258). New UI tests for re-request flow would live here.
- `apps/commercial/tests/test_views.py` — `SubscriptionRenewQuantityTests` (1134) is the precedent; new tests for the relaxed flow belong near it.

## Design Constraints

- **No schema change needed.** No unique constraint on `(customer, service)`, so multiple rows per pair already coexist. A DB migration is **not** required.
- **Statuses:** `requested` / `pending` / `paid` / `expired` (`ServiceSubscription.PAYMENT_STATUS_CHOICES`, models.py:174-179).
- **`is_active` property** (models.py:228-230): `payment_status == 'paid' and end_date and end_date > timezone.now()` — the canonical "active" definition.
- **`compute_end_date`** (models.py:166-170): agrometeo → `+relativedelta(months=quantity)`, else `+timedelta(days=quantity)`. Already used by both `ServiceDetailView.form_valid` (line 137) and `SubscriptionRenewView` (line 152).
- **Project conventions:** soft delete via `record_active` filter (default manager), UUID kwarg in URLs, custom permissions (`commercial.add/change/...`), templates djlint-formatted (2-space), UI in Spanish.

## Approaches

| # | Approach | Pros | Cons | Effort |
|---|----------|------|------|--------|
| **A** | **New requested subscription while old active stays** (follows the renewal precedent) | Consistent with existing `SubscriptionRenewView`; no schema change; user can renew early; minimal diff | Multiple rows per customer+service accumulate; needs UI to tell active vs. requested apart; billing needs to handle the overlap | **Low-Med** |
| **B** | **Replace/deactivate the old active immediately** | Single active row always; cleaner "one active subscription" invariant; simpler lists | Violates renewal precedent; risks deactivating a legitimate paid sub mid-term; requires write on the old row (not just create) — closer to a schema/logic change; destructive | **Med** |
| **C** | **Block only in-flight (requested/pending), allow when paid/active** | The narrowest possible change; still prevents duplicate pending/requested at the same time (the real "double order" risk); paid/active re-request allowed | A user can still open multiple "renewal-like" requests while one is pending only if not blocked — this option keeps that blocked; slightly different semantics from the goal if "re-request even while requested" is required | **Low** |

### Detailed review

**Option A — new requested row while old stays (recommended).**
This is exactly what `SubscriptionRenewView` already does. `ServiceDetailView.form_valid` would drop the `existing` block (or relax it) and create a new `requested` row, letting staff generate a fresh invoice. The `get_context_data` `existing_subscription` should be re-scoped so the template shows the *latest* status but still lets the user submit a new request (turning the alert into informational text plus the form). UI contract tests in `test_services_ui.py` would need updating for the re-request case.

**Option B — replace/deactivate old immediately.**
The opposite of the established renewal behavior. It would require mutating the old row's `record_active`/status on each new request, reintroducing a "single active per service" invariant that the model deliberately does not enforce. Higher risk (touching existing paid data) and more logic. Not recommended given the working renewal precedent.

**Option C — block only requested/pending, allow paid/active.**
The minimal safe relaxation: `form_valid` and the templates would only block while a `requested`/`pending` row exists, while allowing re-request when the existing row is `paid` (active). This satisfies the stated goal ("re-request while active") without opening up arbitrary concurrent duplicates. Lower blast radius than A, but still needs the same template rework (A and C differ mainly in whether `requested` also unblocks).

## Recommendation

**Option A — create a new `requested` subscription while the old active one stays**, aligned with the existing `SubscriptionRenewView` precedent. It is the least surprising, requires **no** schema change, and matches the already-shipped model semantics (no `(customer, service)` uniqueness). 

A pragmatic refinement: block only while a `requested`/`pending` row exists (i.e. combine A + C for the *blocking* rule), and allow submission whenever the latest existing row is `paid`/`expired` or absent. This prevents "double in-flight order" while permitting renewal of an active service. If the product wants true "re-request anytime", drop the block entirely (pure A).

The core mechanical changes are small and localized (relax `form_valid`, rescope `existing_subscription`, update three template conditionals) plus tests. The trickier decisions are product-level, not technical (see Open Questions).

## Risks

- **Double invoicing / billing overlap:** creating many requested rows could generate duplicate invoices for overlapping periods. Needs a product decision (proposal phase). Billing should probably key off the latest row or reject overlapping periods.
- **UI ambiguity:** a client with an active sub needs a clear, distinct "Solicitar de nuevo" / "Renovar" label instead of the current "Ya tienes..." alert. Bad copy could confuse "I have one" vs. "I want another".
- **Staff visibility:** staff list/bulk views iterate subscriptions; more rows per customer could clutter the subscription list. Confirm no performance/UX regression.
- **Existing UI tests:** `test_services_ui.py` and `test_views.py` assertions around the blocking alert/button must be updated; the renew precedent test (`SubscriptionRenewQuantityTests`) should be extended rather than changed.
- **`existing_subscription` rescope:** if it keeps looking at "non-expired", paid rows would still hide the form. The context must distinguish the latest active/paid row from an in-flight one, or drive the template off both flags.

## Open Questions (for the proposal phase)

1. **Billing/duplicates:** should a re-request while active be allowed to overlap the current period, or only start after the current `end_date`? Should the old paid row be linked as a predecessor (like renew logs `f'Suscripción renovada desde {old.uuid}'`)?
2. **UI labels:** exact copy for the re-request CTA ("Solicitar de nuevo" / "Renovar") and for the info alert when active.
3. **Blocking rule:** block only `requested`/`pending`, or allow true anytime re-request (pure A)?
4. **Staff-side:** should `SubscriptionCreateView` also gain any guard, or stay unlimited as today?

## Ready for Proposal

**Yes.** The mapping is fully verified against the real files; the renewal precedent confirms the relaxed model works; no schema change is required. The orchestrator should tell the user that Option A (new requested row while old active stays, with an in-flight block refinement) is recommended, and surface the Open Questions (especially billing/duplicates and UI labels) for the proposal sing.
