# service-re-request — Specification

## Purpose

Allow a client to re-request a commercial service while an active (paid) subscription exists. The active row remains untouched; a new `requested` row is created. Only in-flight (requested/pending) subscriptions block submission. No schema change.

> **Amendment (2026-09-16)**: amended after verify FAIL (`a00188fe`) — this spec describes the behavior actually implemented at HEAD. REQ-05 (public-list ribbons/buttons/precedence) is removed: the public catalog is state-neutral, a behavior owned by the promoted spec `home-public-services-layout` ("Commercial services public card is state-neutral"). REQ-03 S1 and REQ-04 S1 are removed (no covering tests at HEAD). REQ-01 S2 reflects the unified "Solicitar" submit label.

## Requirements

### Requirement: REQ-01: Re-request allowed when active paid subscription exists

The system SHALL allow a client to submit a new service request when a `paid` + `is_active` (`end_date` in the future) subscription already exists for that service. `form_valid` SHALL guard only on `payment_status__in=['requested', 'pending']`. On successful POST the system SHALL create a new `ServiceSubscription` with `payment_status='requested'` and the existing paid row SHALL remain unchanged. The system SHALL redirect to `commercial:suscripcion_list` after creation.

#### Scenario: Re-request with active paid subscription creates new requested row

- GIVEN a client with a `ServiceSubscription` where `payment_status='paid'` and `end_date` is in the future
- WHEN the client POSTs a new request for the same service via `ServiceDetailView`
- THEN a new `ServiceSubscription` with `payment_status='requested'` is created
- AND the existing `paid` row is unchanged (same `payment_status`, `end_date`, `record_active`)
- AND the response redirects to `commercial:suscripcion_list`

#### Scenario: Active paid subscription renders form with active-until alert

- GIVEN a client with a `paid` + active subscription for the service
- WHEN the client visits `ServiceDetailView` (GET)
- THEN the request form IS rendered with submit button labeled "Solicitar"
- AND an informational alert states the subscription is active until `end_date`

### Requirement: REQ-02: Re-request blocked when in-flight subscription exists

The system SHALL block submission when a `ServiceSubscription` with `payment_status` in `['requested', 'pending']` exists for the same customer and service. No new row SHALL be created. A warning message SHALL be displayed and the client SHALL be redirected to `ServiceDetailView`.

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
- AND the client is redirected to `ServiceDetailView`

#### Scenario: Detail view hides form for in-flight subscription

- GIVEN a client with a `requested` or `pending` subscription for the service
- WHEN the client visits `ServiceDetailView` (GET)
- THEN the request form IS NOT rendered
- AND the submit button IS NOT rendered
- AND an alert is displayed without the form

### Requirement: REQ-04: Service detail context splits into two flags

`ServiceDetailView.get_context_data` SHALL set `in_flight_subscription` (the latest `requested`/`pending` row, or `None`) and `active_subscription` (the latest `paid` + `is_active` row, or `None`). The old `existing_subscription` context key SHALL be removed.

#### Scenario: Context with only active paid subscription

- GIVEN a client with only a `paid` active row
- WHEN `ServiceDetailView.get_context_data` runs
- THEN `in_flight_subscription` is `None`
- AND `active_subscription` is the `paid` row

### Requirement: REQ-06: No schema change

The system SHALL NOT require a database migration. Multiple `ServiceSubscription` rows per customer and service already coexist (no unique constraint on `(customer, service)`).

#### Scenario: Feature ships without migrations

- GIVEN the re-request feature implemented at HEAD
- THEN no migration files accompany the change
- AND the `(customer, service)` pairing remains non-unique
