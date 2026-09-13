# commercial-service-categories Specification

## Purpose

Expose `Service.service_category` (`agrometeo`/`pronostico`) as a control in the service create/update forms so staff can choose the billing period category. Previously no template rendered the field, so services always defaulted to `pronostico`. The select SHALL be always visible and follow the `service_type` form pattern, without new `toggleFields()` logic. Applicable to public and commercial services.

## Requirements

### Requirement: Service category select in create form

`apps/commercial/templates/pages/commercial/service/create.html` SHALL render a `<select name="service_category">` iterating `form.fields.service_category.choices`. The select SHALL be always visible (not hidden by `toggleFields()`). If left blank, the value SHALL fall back to the model default.

#### Scenario: Create form shows category select with both options

- GIVEN the rendered `create.html`
- WHEN the HTML is inspected
- THEN it SHALL contain a `service_category` select with `agrometeo` and `pronostico` options
- AND the select SHALL be visible without requiring a `service_type` interaction

#### Scenario: Blank category falls back to default

- GIVEN a service is created with no `service_category` value submitted
- WHEN the form is saved
- THEN `service_category` SHALL be `pronostico` (model default)

### Requirement: Service category select in update form

`apps/commercial/templates/pages/commercial/service/update.html` SHALL render a `<select name="service_category">` iterating `form.fields.service_category.choices`, always visible, preselecting the object's current category value. The image/fslightbox and PDF modal trigger markup SHALL be preserved unchanged.

#### Scenario: Update form preselects current category

- GIVEN an object with `service_category='agrometeo'` is rendered in `update.html`
- WHEN the HTML is inspected
- THEN the `service_category` option `agrometeo` SHALL be `selected`
- AND the select SHALL be visible without requiring a `service_type` interaction

#### Scenario: File preview invariants preserved in update form

- GIVEN the rendered `update.html` with an image and a PDF object present
- WHEN the HTML is inspected
- THEN it SHALL contain `data-fslightbox="gallery"` for the image
- AND it SHALL contain `data-pdf-url=` for the PDF trigger
- AND neither SHALL reference `target="_blank"` pointing at a file URL

### Requirement: Category select applies to public and commercial services

The `service_category` select SHALL be present regardless of `service_type` (public or commercial), and no new `toggleFields()` logic SHALL be added to show or hide it.

#### Scenario: Select visible for both service types

- GIVEN `create.html` or `update.html` is rendered
- WHEN the code toggles between `public` and `commercial` service types
- THEN the `service_category` select SHALL remain visible in both states

### Requirement: Public card exposes category badge and discrete code

`commercial_public.html` SHALL renderizar el badge de categoría (`service.get_service_category_display()`: "Agrometeorológico"/"Pronóstico") y el `service.code` de forma discreta (p. ej. "Código: C200") solo si existe, como referencia para facturas.

#### Scenario: Badge y código visibles

- GIVEN servicio comercial con `service_category='agrometeo'` y code='C200'
- WHEN se renderiza el card público
- THEN aparece el badge "Agrometeorológico"
- AND el texto "Código: C200" está presente

#### Scenario: Sin código no se muestra etiqueta

- GIVEN servicio comercial sin `code`
- WHEN se renderiza el card público
- THEN no hay etiqueta "Código:"

## Coverage Notes

- No model changes, no data migration; default `pronostico` stays the model's default.
- Commercial services billing layout is out of scope; only the service form exposes the category.
- Preserves invariants REQ-001/002/004 from spec `018-dashboard-file-preview-modal`.
