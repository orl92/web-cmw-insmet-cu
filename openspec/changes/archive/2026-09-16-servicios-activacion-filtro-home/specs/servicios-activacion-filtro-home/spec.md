# servicios-activacion-filtro-home Specification

## Purpose

Los servicios usan soft delete: desactivar solo afectaba al dashboard, el portal público seguía mostrando los desactivados y no había forma de reactivarlos. Al editar se podía cambiar el tipo público/comercial y el listado mostraba `$0.00` en servicios públicos.

## Requirements

### Requirement: Public services list filters out inactive records

`PublicServicesListView.get_queryset()` SHALL filter `record_active=True` y `service_type=Service.PUBLIC`.

#### Scenario: Inactive public service is hidden from the home list

- GIVEN a public service with `record_active=False`
- WHEN the public services list is rendered
- THEN the service SHALL NOT appear

### Requirement: Public commercial services list filters out inactive records

`PublicCommercialServicesListView.get_queryset()` SHALL filter `record_active=True` y `service_type=Service.COMMERCIAL`.

#### Scenario: Inactive commercial service is hidden from the public list

- GIVEN a commercial service with `record_active=False`
- WHEN the public commercial services list is rendered
- THEN the service SHALL NOT appear

### Requirement: Commercial service detail requires an active record

`ServiceDetailView.dispatch()` SHALL usar `get_object_or_404` con `record_active=True`; `related_services` SHALL filtrar igual.

#### Scenario: Detail and related services exclude inactive records

- GIVEN a commercial service with `record_active=False`
- WHEN the detail page is requested
- THEN the response SHALL be 404
- AND `related_services` SHALL only contain active services

### Requirement: Reactivate a service from the dashboard list

`ServiceReactivateView` (POST, `permission_required='commercial.change_service'`) SHALL set `record_active=True` y `deleted_at=None` (sin `_cleanup_files`), log `CHANGE` y redirect con éxito. El listado SHALL mostrar un botón verde "Reactivar" solo si `not object.record_active and perms.commercial.change_service`.

#### Scenario: Staff reactivates a deactivated service

- GIVEN a service with `record_active=False`, `deleted_at` set
- WHEN the staff POSTs to the reactivate URL
- THEN `record_active` SHALL be `True` and `deleted_at` SHALL be `None`

#### Scenario: Reactivate button gated by state and permission

- GIVEN the service list
- WHEN a row is inactive and the user has `change_service`
- THEN the row SHALL contain a reactivate control
- AND an active row SHALL NOT contain it

#### Scenario: Reactivating an already active service is a no-op warning

- GIVEN a service with `record_active=True`
- WHEN a POST reaches the reactivate URL
- THEN the view SHALL warn and SHALL NOT change state

### Requirement: Service type is immutable when editing

En `update.html`, el select `service_type` SHALL ir disabled con hidden input del valor actual; `ServiceUpdateView.post()` SHALL forzar el tipo original y la limpieza de PDF SHALL ser removida.

#### Scenario: Update form shows a disabled type selector

- GIVEN the service update form
- WHEN the HTML is inspected
- THEN the `service_type` select SHALL have the `disabled` attribute
- AND a hidden `service_type` input SHALL carry the current value

#### Scenario: POST cannot change the service type

- GIVEN an update POST with a tampered `service_type`
- WHEN the form is validated
- THEN the saved instance SHALL keep its original `service_type`

### Requirement: Public rows show no price nor subscriptions in the dashboard list

En `list.html`, para `service_type == 'public'` las celdas Precio y Suscripciones SHALL renderizar `—` muted; los comerciales SHALL mantener precio vía `format_cup` y `num_subscriptions`.

#### Scenario: Public row shows em dash in price and subscriptions

- GIVEN a public service in the dashboard list
- WHEN the HTML is inspected
- THEN the Precio and Suscripciones cells SHALL contain a muted `—`
- AND SHALL NOT contain `$` nor a number

#### Scenario: Commercial row keeps price and subscriptions

- GIVEN a commercial service in the dashboard list
- WHEN the HTML is inspected
- THEN the Precio cell SHALL contain `$` and the price
- AND the Suscripciones cell SHALL contain the subscription count

## Coverage Notes

- No hay cambios de modelo ni migraciones.
- REQ-6 equal-height cards (`h-100`) fue retirado: la clase no existe en los templates de HEAD y el maintainer decidió no implementarla. Layout real: `col-md-6` side-by-side (imagen full-width en comerciales), sin garantía de igual altura.
- Reactivación acotada a servicios; otros modelos podrían adoptarla luego.
