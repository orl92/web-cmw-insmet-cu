# service-re-request — Specification

## Purpose

Allow a client to re-request a commercial service while an active (paid) subscription exists. The active row remains untouched; a new `requested` row is created. Only in-flight (requested/pending) subscriptions block submission. No schema change.

## Requirements

### REQ-01: Re-request allowed when active paid subscription exists

The system SHALL allow a client to submit a new service request when a `paid` + `is_active` (end_date in the future) subscription already exists for that service. `form_valid` SHALL guard only on `payment_status__in=['requested', 'pending']`. On successful POST the system SHALL create a new `ServiceSubscription` with `payment_status='requested'` and the existing paid row SHALL remain unchanged. The system SHALL redirect to `commercial:suscripcion_list` after creation.

#### Scenario: Re-request with active paid subscription creates new requested row

- GIVEN a client with a `ServiceSubscription` where `payment_status='paid'` and `end_date` is in the future
- WHEN the client POSTs a new request for the same service via `ServiceDetailView`
- THEN a new `ServiceSubscription` with `payment_status='requested'` is created
- AND the existing `paid` row is unchanged (same `payment_status`, `end_date`, `record_active`)
- AND the response redirects to `commercial:suscripcion_list`

#### Scenario: Active paid subscription does not block the form

- GIVEN a client with a `paid` + active subscription for the service
- WHEN the client visits `ServiceDetailView` (GET)
- THEN the request form IS rendered
- AND the submit button label is "Solicitar de nuevo"
- AND an informational alert states the subscription is active until `end_date`

### REQ-02: Re-request blocked when in-flight subscription exists

The system SHALL block submission when a `ServiceSubscription` with `payment_status` in `['requested', 'pending']` exists for the same customer and service. No new row SHALL be created. A warning message SHALL be displayed.

#### Scenario: Blocked when requested subscription exists

- GIVEN a client with a `ServiceSubscription` where `payment_status='requested'`
- WHEN the client POSTs a new request for the same service
- THEN no new `ServiceSubscription` is created (row count unchanged)
- AND a warning message is displayed
- AND the client is redirected to `ServiceDetailView`

#### Scenario: Blocked when pending subscription exists

- GIVEN a client with a `ServiceSubscription` where `payment_status='pending'`
- WHEN the client POSTs a new request for the same service
- THEN no new `ServiceSubscription` is created
- AND a warning message is displayed

#### Scenario: Detail view hides form for in-flight subscription

- GIVEN a client with a `requested` or `pending` subscription for the service
- WHEN the client visits `ServiceDetailView` (GET)
- THEN the request form is NOT rendered
- AND the submit button is NOT rendered
- AND an alert is displayed without the form

### REQ-03: Empty state — normal request path unchanged

When no subscription rows exist for a customer and service, the system SHALL behave exactly as today: the request form renders and a POST creates the first `requested` row.

#### Scenario: First request with no existing subscriptions

- GIVEN a client with zero `ServiceSubscription` rows for the service
- WHEN the client POSTs a new request
- THEN a single `ServiceSubscription` with `payment_status='requested'` is created
- AND the response redirects to `commercial:suscripcion_list`

### REQ-04: Service detail context splits into two flags

`ServiceDetailView.get_context_data` SHALL set `in_flight_subscription` (the latest `requested`/`pending` row, or `None`) and `active_subscription` (the latest `paid` + `is_active` row, or `None`). The old `existing_subscription` context key SHALL be removed.

#### Scenario: Context exposes both flags independently

- GIVEN a client with both a `paid` active row and a `requested` row for the same service
- WHEN `ServiceDetailView.get_context_data` runs
- THEN `in_flight_subscription` is the `requested` row
- AND `active_subscription` is the `paid` row

#### Scenario: Context with only active paid subscription

- GIVEN a client with only a `paid` active row
- WHEN `ServiceDetailView.get_context_data` runs
- THEN `in_flight_subscription` is `None`
- AND `active_subscription` is the `paid` row

### REQ-05: Public list — deterministic per-service button state

`PublicCommercialServicesListView` SHALL resolve `user_subscriptions` per service using precedence: `requested`/`pending` (in-flight) > `paid` active > `expired`/none. The button and ribbon in `commercial_public.html` SHALL reflect the resolved status deterministically.

#### Scenario: Active paid subscription shows "Solicitar de nuevo"

- GIVEN a client with a `paid` + active subscription for a service
- WHEN the public service list renders
- THEN the ribbon shows "Activo"
- AND the button text is "Solicitar de nuevo"

#### Scenario: Requested/pending subscription shows no request button

- GIVEN a client with a `requested` subscription for a service
- WHEN the public service list renders
- THEN the ribbon shows "Solicitado"
- AND no request button is rendered

#### Scenario: Pending subscription shows "Ver factura"

- GIVEN a client with a `pending` subscription for a service
- WHEN the public service list renders
- THEN the button text is "Ver factura"

#### Scenario: Expired or no subscription shows "Solicitar"

- GIVEN a client with only an `expired` subscription or no subscription for a service
- WHEN the public service list renders
- THEN the button text is "Solicitar"

#### Scenario: Multiple rows — precedence resolves to highest priority

- GIVEN a client with both a `paid` active row and a `requested` row for the same service
- WHEN the public service list renders
- THEN the resolved status is `requested` (in-flight wins over active)
- AND the button/ribbon reflect the `requested` state

### REQ-06: No schema change

The system SHALL NOT require a database migration. Multiple `ServiceSubscription` rows per customer and service already coexist (no unique constraint on `(customer, service)`).
