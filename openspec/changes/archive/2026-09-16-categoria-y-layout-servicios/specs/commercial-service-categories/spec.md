# commercial-service-categories Specification

## Purpose

Expose `Service.service_category` (`agrometeo`/`pronostico`) as a control in the service create/update **admin** forms so staff can choose the billing period category. Previously no template rendered the field, so services always defaulted to `pronostico`.

Per product decision (2026-09-04):
- The category select SHALL be **visible only when `service_type == 'commercial'`**. For **public** services, the select SHALL be **hidden** (and its value not forced; model default `pronostico` applies).
- In the service create/update form, for **public** services, the **PDF and image fields SHALL render side by side** (two `col-md-6` columns). For **commercial** services, only the image field renders, at full width, unchanged from current behavior.
- **Image required for public services**: the public form SHALL require an image with the same visible feedback (required label, `required` attribute) as the other required fields, and the backend form SHALL reject a public service without image (create and update, using the existing `existing_image` pattern).
- **Balanced first row**: in create/update forms, `title` and `service_type` SHALL render side by side as two `col-md-6` columns.
- **Commercial fields in one balanced row**: for `commercial`, `service_category`, `code` and `price` SHALL render side by side as three `col-md-4` columns, in that order (category first, then code, then price), replacing the previous `col-md-6`+`col-md-6`/separate-row layout.

## Requirements

### Requirement: Category select visible only for commercial type in create form

`apps/commercial/templates/pages/commercial/service/create.html` SHALL render a `<select name="service_category">` iterating `form.fields.service_category.choices` inside a container controlled by `toggleFields()`. The container SHALL be hidden by default and SHALL only become visible when `service_type == 'commercial'`. For `public`, the container SHALL remain hidden and the input disabled. When no value is submitted, `service_category` SHALL fall back to the model default.

#### Scenario: Create form hides category select for public type

- GIVEN `create.html` is rendered
- WHEN the service type is `public`
- THEN the `service_category` select container SHALL be hidden (`display: none`) and the input disabled

#### Scenario: Create form shows category select for commercial type

- GIVEN `create.html` is rendered
- WHEN the service type is `commercial`
- THEN the `service_category` select SHALL be visible with `agrometeo` and `pronostico` options

#### Scenario: Blank category falls back to default

- GIVEN a service is created with no `service_category` value submitted
- WHEN the form is saved
- THEN `service_category` SHALL be `pronostico` (model default)

### Requirement: Category select visible only for commercial type in update form

`apps/commercial/templates/pages/commercial/service/update.html` SHALL render a `<select name="service_category">` iterating `form.fields.service_category.choices`, controlled by `toggleFields()`, visible only for `service_type == 'commercial'`, preselecting the object's current category value. The image/fslightbox and PDF modal trigger markup SHALL be preserved unchanged.

#### Scenario: Update form hides category select for public type

- GIVEN an object with `service_type == 'public'` is rendered in `update.html`
- WHEN the HTML is inspected
- THEN the `service_category` select SHALL be hidden and disabled

#### Scenario: Update form preselects current category for commercial type

- GIVEN an object with `service_type == 'commercial'` and `service_category='agrometeo'` is rendered in `update.html`
- WHEN the HTML is inspected
- THEN the `service_category` select SHALL be visible
- AND the option `agrometeo` SHALL be `selected`

#### Scenario: File preview invariants preserved in update form

- GIVEN the rendered `update.html` with an image and a PDF object present
- WHEN the HTML is inspected
- THEN it SHALL contain `data-fslightbox="gallery"` for the image
- AND it SHALL contain `data-pdf-url=` for the PDF trigger
- AND neither SHALL reference `target="_blank"` pointing at a file URL

### Requirement: Public services render PDF and image side by side in the form

In `create.html`/`update.html`, when `service_type == 'public'`, the PDF field and the image field SHALL render inside a `row` as two `col-md-6` columns (side by side). For `service_type == 'commercial'`, the image SHALL render at full width without the PDF column.

#### Scenario: Public form shows PDF and image in two columns

- GIVEN the service form with `service_type == 'public'`
- WHEN the HTML is inspected
- THEN `field_pdf` and `field_image` SHALL be present
- AND both SHALL be inside a row as `col-md-6` columns

#### Scenario: Commercial form keeps image alone at full width

- GIVEN the service form with `service_type == 'commercial'`
- WHEN the HTML is inspected
- THEN the PDF field SHALL be hidden
- AND the image field SHALL NOT be constrained to `col-md-6` (full width as today)

### Requirement: Image required for public services

`ServiceForm.clean()` SHALL reject public services submitted without an image, unless the instance already carries one (`existing_image`). The rendered create/update forms SHALL mark the image label/input as required for public services without an existing image, showing the same `required` marker and error feedback as the other required fields.

#### Scenario: Create form requires image for public

- GIVEN `create.html` is rendered
- WHEN the HTML is inspected
- THEN the `image` input SHALL carry the `required` attribute
- AND the image label SHALL carry the `required` class

#### Scenario: Update form requires image only when missing

- GIVEN an update form with no existing image
- WHEN the HTML is inspected
- THEN the `image` input SHALL carry the `required` attribute
- AND the image label SHALL carry the `required` class

- GIVEN an update form with an existing image
- WHEN the HTML is inspected
- THEN the `image` input SHALL NOT carry the `required` attribute (blank keeps the current image)

#### Scenario: Backend rejects public service without image

- GIVEN a public service submitted without `image` and without an existing image
- WHEN the form is validated
- THEN `form.errors` SHALL include `image`

### Requirement: Balanced first row (title + type)

In `create.html`/`update.html`, `title` and `service_type` SHALL render inside the same row as two `col-md-6` columns (replacing the previous `col-md-8`/`col-md-4` split).

#### Scenario: Create and update render title and type 6/6

- GIVEN the service form
- WHEN the HTML is inspected
- THEN the `title` field container SHALL be `col-md-6`
- AND the `service_type` field container SHALL be `col-md-6`

### Requirement: Commercial fields in one balanced row (category, code, price)

In `create.html`/`update.html`, for commercial services, `service_category`, `code` and `price` SHALL render inside the same row as three `col-md-4` columns, in that order (category first, then code, then price).

#### Scenario: Create renders commercial fields 4/4/4 in order

- GIVEN the service form
- WHEN the HTML is inspected
- THEN `field_category`, `field_code` and `field_price` SHALL be `col-md-4` containers
- AND they SHALL appear in the document in that order (category before code, code before price)

## Coverage Notes

- No model changes, no data migration; default `pronostico` stays the model's default.
- The public-facing list/detail templates (`public.html`, `service_detail.html`, `commercial*.html`) are intentionally out of scope and remain unchanged.
- Preserves invariants REQ-001/002/004 from spec `018-dashboard-file-preview-modal`.
- Reuses the existing `toggleFields()` JS pattern; no new JS file.
