---
change: 022-servicios-comerciales-por-tipo
requirement: commercial-service-categories
version: 1.0.0
---

# Commercial Service Categories

## Purpose

Categorize commercial services by billing type (agrometeorological = monthly, forecast = daily), deriving the billing period and subscription end date from the category, and billing by quantity of months/days instead of a free date range.

## Requirements

### Requirement: Service category derives billing period

`Service` MUST expose a `service_category` field with choices `agrometeo` ("Agrometeorológico") and `pronostico` ("Pronóstico"), defaulting to `pronostico`. The billing period MUST be derived from the category: `agrometeo` → monthly (1 month), `pronostico` → daily (1 day). There SHALL NOT be a per-service `billing_period` field.

#### Scenario: Default category preserves daily behavior

- GIVEN a commercial `Service` with no explicit category
- WHEN the service is created
- THEN `service_category` is `pronostico`
- AND its billing period is daily (1 day)

#### Scenario: Agrometeorological category maps to monthly

- GIVEN a commercial `Service` with `service_category = 'agrometeo'`
- WHEN the billing period is resolved
- THEN the period is 1 month

### Requirement: End date derived from quantity and category

`ServiceSubscription.quantity` MUST be an IntegerField holding months (agrometeo) or days (pronostico). `end_date` MUST be computed as `start_date + quantity × period(category)` using month-aware arithmetic (e.g. `dateutil.relativedelta`) so month-end overflow does not corrupt the date.

#### Scenario: Monthly end date from quantity

- GIVEN a subscription with category `agrometeo`, `quantity = 2` and `start_date = 2026-01-31`
- WHEN `end_date` is computed
- THEN `end_date` is `2026-03-31` (no overflow to an invalid date)

#### Scenario: Daily end date from quantity

- GIVEN a subscription with category `pronostico`, `quantity = 5` and `start_date = 2026-01-01`
- WHEN `end_date` is computed
- THEN `end_date` is `2026-01-06`

### Requirement: Invoice amount uses quantity times price

Invoice amount MUST be computed as `quantity × price`, replacing the previous `days_count × price`. This MUST apply in `process_batch_invoice`, `process_manual_invoice`, and the subscription request form. `start_date` is chosen by the client; `end_date` is derived from quantity and period.

#### Scenario: Batch invoice amount

- GIVEN a subscription with `quantity = 3`, `price = 100` and category `monthly`
- WHEN the invoice is generated
- THEN the `importe` is `300`

#### Scenario: Manual invoice amount

- GIVEN a subscription with `quantity = 10`, `price = 5` and category `daily`
- WHEN the invoice is generated manually
- THEN the `importe` is `50`

### Requirement: Subscription form conditioned by category

The subscription request form MUST prompt for `quantity` labeled by the service category: "cantidad de meses" for `agrometeo` and "cantidad de días" for `pronostico`. It SHALL NOT ask for a free date range of `start_date`/`end_date`; the client only chooses `start_date` and `quantity`.

#### Scenario: Forecast service shows days

- GIVEN a service with category `pronostico`
- WHEN the request form renders
- THEN the quantity field is labeled "cantidad de días"
- AND no free date-range inputs are shown

#### Scenario: Agrometeorological service shows months

- GIVEN a service with category `agrometeo`
- WHEN the request form renders
- THEN the quantity field is labeled "cantidad de meses"

### Requirement: Corrected subscription permission

The AJAX invoice endpoint MUST check `commercial.view_subscription` instead of the nonexistent `commercial.view_servicesubscription`. Authenticated staff MUST receive subscription data rather than a 403.

#### Scenario: Staff AJAX returns data

- GIVEN an authenticated staff user with subscription view permission
- WHEN calling `ajax_pending_subscriptions`
- THEN the response is 200 with the pending-subscription data
- AND no AttributeError/permission error is raised

### Requirement: Staff edit/create buttons on public view

When the viewer `is_staff` or has `commercial.change_service`, the public commercial view SHALL show an "Editar" button (→ `commercial:servicio_update <service.uuid>`) and a "Nuevo servicio" link (→ `commercial:servicio_create`). Existing client/anonymous buttons and ribbons SHALL remain unchanged.

#### Scenario: Staff sees management actions

- GIVEN a staff user viewing the public commercial page
- WHEN the page renders
- THEN an "Editar" button and a "Nuevo servicio" link are present
- AND existing ribbon for staff is preserved

#### Scenario: Anonymous viewer sees no management actions

- GIVEN an anonymous user viewing the public commercial page
- WHEN the page renders
- THEN no "Editar" button or "Nuevo servicio" link is shown
- AND the existing anonymous ribbon is preserved

### Requirement: Service detail shows category and period price

The service detail view SHALL display the category (Agrometeorológico/Diario) and the price per period (per month for `agrometeo`, per day for `pronostico`).

#### Scenario: Detail shows monthly price

- GIVEN a service with category `agrometeo` and `price = 120`
- WHEN the detail page renders
- THEN the category "Agrometeorológico" and a per-month price of `120` are shown

#### Scenario: Detail shows daily price

- GIVEN a service with category `pronostico` and `price = 10`
- WHEN the detail page renders
- THEN the category "Diario" and a per-day price of `10` are shown

### Requirement: Pending subscription guidance without QR

In the public commercial view, a subscription in `pending` state with a non-QR payment method SHALL show guidance text or a link to view the invoice, instead of no button.

#### Scenario: Pending non-QR shows guidance

- GIVEN a subscription in `pending` state with a non-QR method
- WHEN the public commercial page renders
- THEN guidance text or a "ver factura" link is shown

### Requirement: Data migration for existing services

Existing commercial `Service` rows MUST receive `service_category = 'pronostico'`, preserving current daily behavior. The migration MUST be safe and use a default.

#### Scenario: Existing services migrate to forecast

- GIVEN existing commercial services created before this change
- WHEN the data migration runs
- THEN each row has `service_category = 'pronostico'`
