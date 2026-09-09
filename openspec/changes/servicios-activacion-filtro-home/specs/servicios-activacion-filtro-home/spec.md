# servicios-activacion-filtro-home Specification

## Purpose

Los servicios usan soft delete (`record_active`, `SoftDeleteModel`). Hoy desactivar solo afecta al dashboard: el portal público sigue mostrando los servicios desactivados. Tampoco existe forma de reactivarlos. Además, el formulario de edición permite cambiar el tipo público/comercial (con lógica extraña para limpiar PDF), las cards PDF/imagen no tienen la misma altura, y el listado muestra `$0.00` en servicios públicos que no tienen precio.

## Requirements

### Requirement: Public services list filters out inactive records

`apps/home/views/servicios/publicos/views.py` `PublicServicesListView.get_queryset()` SHALL filter `record_active=True` in addition to `service_type=Service.PUBLIC`.

#### Scenario: Inactive public service is hidden from the home list

- GIVEN a public service with `record_active=False`
- WHEN the public services list is rendered
- THEN the service SHALL NOT appear

### Requirement: Public commercial services list filters out inactive records

`apps/home/views/servicios/comerciales/views.py` `PublicCommercialServicesListView.get_queryset()` SHALL filter `record_active=True` in addition to `service_type=Service.COMMERCIAL`.

#### Scenario: Inactive commercial service is hidden from the public commercial list

- GIVEN a commercial service with `record_active=False`
- WHEN the public commercial services list is rendered
- THEN the service SHALL NOT appear

### Requirement: Commercial service detail requires an active record

`ServiceDetailView.dispatch()` SHALL `get_object_or_404` with `record_active=True`; `related_services` SHALL also filter `record_active=True`.

#### Scenario: Detail and related services exclude inactive records

- GIVEN a commercial service with `record_active=False`
- WHEN the detail page is requested
- THEN the response SHALL be 404
- AND `related_services` SHALL only contain active services

### Requirement: Reactivate a service from the dashboard list

A new `ServiceReactivateView` (POST, `permission_required='commercial.change_service'`) SHALL set `record_active=True` and `deleted_at=None` on a deactivated service (without `_cleanup_files`), log `CHANGE`, and redirect with a success message. The service list template SHALL show a green "Reactivar" button (confirmed via the existing modal) only when `not object.record_active and perms.commercial.change_service`.

#### Scenario: Staff reactivates a deactivated service

- GIVEN a service with `record_active=False`, `deleted_at` set
- WHEN the staff POSTs to the reactivate URL
- THEN `record_active` SHALL be `True` and `deleted_at` SHALL be `None`

#### Scenario: Reactivate button is rendered only for inactive services and permitted staff

- GIVEN the dashboard list of services
- WHEN a row has `record_active=False` and the user has `change_service`
- THEN the row SHALL contain a reactivate control
- AND a row with `record_active=True` SHALL NOT contain it

#### Scenario: Reactivating an already active service is a no-op warning

- GIVEN a service with `record_active=True`
- WHEN a POST reaches the reactivate URL
- THEN the view SHALL show a warning and not change state

### Requirement: Service type is immutable when editing

In `update.html` the `service_type` select SHALL be rendered disabled with a hidden input carrying the current value; `ServiceUpdateView.post()` SHALL force `service_type` to the object's original value before validation, and the existing PDF-clearing logic SHALL be removed.

#### Scenario: Update form shows a disabled type selector

- GIVEN the service update form
- WHEN the HTML is inspected
- THEN the `service_type` select SHALL have the `disabled` attribute
- AND a hidden `service_type` input SHALL carry the current value

#### Scenario: POST cannot change the service type

- GIVEN an update POST with a tampered `service_type`
- WHEN the form is validated
- THEN the saved instance SHALL keep its original `service_type`

### Requirement: PDF and image cards have equal height

In `create.html` and `update.html`, the PDF and image cards SHALL carry `h-100` so both columns render with equal height.

#### Scenario: Both file cards use h-100

- GIVEN the service create/update form
- WHEN the HTML is inspected
- THEN `field_pdf` and `field_image` cards SHALL contain class `h-100`

### Requirement: Public services show no price nor subscriptions in the dashboard list

In `apps/commercial/templates/pages/commercial/service/list.html`, when `service_type == 'public'` the Precio and Suscripciones cells SHALL render `<span class="text-muted">—</span>`; commercial rows SHALL keep `${{ object.price|floatformat:2 }}` and `{{ object.num_subscriptions }}`.

#### Scenario: Public row shows em dash in price and subscriptions

- GIVEN a public service in the dashboard list
- WHEN the HTML is inspected
- THEN the Precio and Suscripciones cells SHALL contain `—` muted
- AND they SHALL NOT contain `$` nor a number

#### Scenario: Commercial row keeps price and subscriptions

- GIVEN a commercial service in the dashboard list
- WHEN the HTML is inspected
- THEN the Precio cell SHALL contain `$` and the price
- AND the Suscripciones cell SHALL contain the subscription count

## Coverage Notes

- No model changes, no migrations.
- The reactivation pattern is intentionally scoped to services; other models (Customer/Contract/Certificate/Subscription) may adopt it later.
- Files public templates themselves are not modified; only the querysets change.
- Existing `toggleFields()` in create/update is reused; removing the editable type only locks the update form, create still lets the user choose the type.