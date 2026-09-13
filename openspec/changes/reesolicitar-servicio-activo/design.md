# Design: Reesolicitar servicio con suscripción activa

## Technical Approach

Relax the client-facing blocking rule in `ServiceDetailView` from "any non-expired subscription" to "only in-flight (`requested`/`pending`)". When the user has an **active** (`paid` + `end_date` future) subscription, allow submitting a new request that creates a new `requested` row, leaving the active one untouched — mirroring the existing `SubscriptionRenewView` precedent. Split the detail context into `in_flight_subscription` (blocks the form) vs `active_subscription` (informs, does not block), and make the public list's per-service button state deterministic. No schema change, no migration.

## Architecture Decisions

### Decision: Block only in-flight requests in `form_valid`

| Option | Tradeoff | Decision |
|---|---|---|
| Keep `.exclude(payment_status='expired')` | Paid rows still block re-request — does not meet goal | ❌ |
| `.exclude(expired)` + allow all | Allows concurrent duplicate in-flight requests (double-order risk) | ❌ |
| `.filter(payment_status__in=['requested','pending'])` | Prevents double in-flight; allows re-request when active/expired | ✅ |

**Choice**: `form_valid` guards on `payment_status__in=['requested', 'pending']`, mirroring renewal semantics. A paid active row no longer blocks.

### Decision: Split `existing_subscription` into two flags

| Option | Tradeoff | Decision |
|---|---|---|
| Keep single `existing_subscription` (any non-expired) | Paid rows would still hide the form in the template | ❌ |
| `in_flight_subscription` + `active_subscription` | Cleanly separates "blocks form" from "informs only" | ✅ |

**Choice**: `get_context_data` sets `in_flight_subscription` (requested/pending, blocks) and `active_subscription` (paid + `is_active`, informational). Drop the old `existing_subscription` key; templates switch to the two new flags.

### Decision: Deterministic per-service state in the list

**Choice**: `PublicCommercialServicesListView.get_context_data` replaces the dict comprehension `{sub.service_id: sub}` with a per-service resolver that picks the highest-precedence row: `requested`/`pending` (in-flight) > `paid` active > `expired`/none. Keeps `user_subscriptions[service.id]` as a single resolved object, so `commercial_public.html` branches per status as today — no template loop change for selection.

## Data Flow

```
[Client portal]
  ServiceDetailView.form_valid
     ├─ existing requested/pending? ──→ warning + redirect (no row)
     └─ else ──→ ServiceSubscription.objects.create(payment_status='requested')
                  (existing paid row untouched)

ServiceDetailView.get_context_data
  subs(customer, service) → in_flight (requested/pending)  → blocks form
                          → active (paid + is_active)      → info alert only

PublicCommercialServicesListView.get_context_data
  subs(customer) → per service: pick precedence requested/pending > paid.active > other
    → user_subscriptions[service.id] (single resolved row)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `apps/home/views/servicios/comerciales/views.py` | Modify | `form_valid` guard → `payment_status__in=['requested','pending']`; split `existing_subscription` into `in_flight_subscription`/`active_subscription`; deterministic `user_subscriptions` resolver in `PublicCommercialServicesListView` |
| `apps/home/templates/pages/home/services/service_detail.html` | Modify | Branch on `in_flight_subscription` (alert, no form) vs `active_subscription` (info alert + form + "Solicitar de nuevo") vs neither (default form) |
| `apps/home/templates/pages/home/services/commercial_public.html` | Modify | Add "Solicitar de nuevo" button + ribbon "Activo" for active; no button for in-flight; keep pending/requested/expired branches |
| `apps/home/tests/test_services_ui.py` | Modify | New re-request UI tests; update `ServicesCommercialStaffButtonTests` for the new button |
| `apps/commercial/tests/test_views.py` | Modify | New `form_valid` tests for active re-request and in-flight block |

## Interfaces / Contracts

Context keys exposed by `ServiceDetailView`:

```python
# SERVICE DETAIL
context['in_flight_subscription']  # ServiceSubscription | None — requested/pending, BLOCKS form
context['active_subscription']     # ServiceSubscription | None — paid + is_active, informs only
# OLD KEY REMOVED: context['existing_subscription']

# PUBLIC LIST (unchanged key, resolved deterministically)
context['user_subscriptions']      # {service_id: resolved_row} — precedence requested/pending > paid.active
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit (commercial) | `form_valid` creates `requested` row alongside active `paid` row; active stays untouched | `test_views.py`: POST detail with active sub → assert new `requested` + old `paid` intact |
| Unit (commercial) | `form_valid` blocked when `requested`/`pending` exists; no new row, warning message | `test_views.py`: assert unchanged row count + message |
| UI (home) | Active sub renders form + "Solicitar de nuevo" + info alert | `test_services_ui.py`: assert form present, no "Ya tienes" block |
| UI (home) | Requested/pending sub renders alert without form/button | `test_services_ui.py`: assert form absent |
| Regression | `ServicesCommercialStaffButtonTests` (pending shows "Ver factura"), `ServicesVisibilityFilterTests` | Verify suite stays green; the `subscriptions = 2` setup in `ServicesCommercialUiTests` unaffected (uses `commercial.html`, not detail) |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary. This change is limited to Django view logic and template branches.

## Migration / Rollout

No migration required. No data mutation — only new rows are created (matching the renewal precedent). Rollback: revert the commit; restores the any-non-expired block and original templates; no rows are ever mutated, only created.

## Open Questions

- [ ] None blocking — product copy ("Solicitar de nuevo") already confirmed by proposal; billing overlap handled by staff as today.
