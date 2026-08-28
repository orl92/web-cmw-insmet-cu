# Spec — File Preview Consistency Modal (018-dashboard-file-preview-modal)

Delta requirements establishing a single, project-wide preview integration for
file fields on dashboard edit/create forms. Reuses existing vendored assets
(`includes/home/document_pdf_modal.html`, `static/dist/js/document-modal.js`,
`static/dist/libs/fslightbox/index.js`); no new libraries, no capability or
model changes.

## Requirements

### Requirement: REQ-001 — PDF fields open the shared modal, never a new tab

Every dashboard edit/create form that renders a PDF file field (e.g.
`object.pdf.url`, `object.file.url`) SHALL provide a "Ver PDF" trigger that opens
the shared `#documentPdfModal` via
`data-bs-toggle="modal" data-bs-target="#documentPdfModal" data-pdf-url="<url>"`,
and SHALL NOT navigate to the file in a new browser tab (`target="_blank"` or a
raw file-URL link).

#### Scenario: PDF trigger present and no new-tab link

- GIVEN the rendered `commercial/service/update.html`, `commercial/subscription/upload_certificate.html`, `publications/update.html`, `meteo/warning/_form.html`, or `meteo/weather_report/_form.html` with a PDF object present
- WHEN the HTML is inspected
- THEN the response SHALL contain a `data-pdf-url=` trigger for that PDF
- AND the response SHALL NOT contain `target="_blank"` pointing to a file URL

### Requirement: REQ-002 — Image fields open fslightbox, never a new tab

Every dashboard edit/create form that renders an image field SHALL provide a
"Ver imagen" trigger using the vendored `fslightbox`
(`<a data-fslightbox="gallery" href="<image_url>">`), and SHALL NOT open the
image directly in a new browser tab (`target="_blank"`).

#### Scenario: Image trigger present and no new-tab link

- GIVEN the rendered `commercial/service/update.html` (image) or `user_auth/profile/update.html` (avatar) with the image object present
- WHEN the HTML is inspected
- THEN the response SHALL contain a `data-fslightbox` anchor for that image
- AND the response SHALL NOT contain `target="_blank"` pointing to an image URL

### Requirement: REQ-003 — form.html exposes the shared preview infra on every form page

`templates/layouts/form.html` SHALL re-expose `{% block modal %}` and, within
`{% block content %}`, include `includes/home/document_pdf_modal.html` plus load
`static/dist/js/document-modal.js` and `static/dist/libs/fslightbox/index.js`, so
the modal markup and both scripts are present on every form page. The scripts
MUST NOT live in `{% block extrajs %}` (child templates override it without
`{{ block.super }}` and would drop them).

#### Scenario: Modal markup and scripts present on a form page

- GIVEN any dashboard form page rendered through `templates/layouts/form.html`
- WHEN the HTML is inspected
- THEN it SHALL contain `documentPdfModal`
- AND it SHALL load the `fslightbox/index.js` script (enabling `data-fslightbox` anchors)
- AND it SHALL load the `document-modal.js` script that wires `data-pdf-url` triggers to the modal

### Requirement: REQ-004 — Single identical integration pattern across all affected templates

The PDF/modal trigger and the image/fslightbox trigger SHALL use the same markup
pattern on all six affected templates, differing only in the resolved URL and
title. No template SHALL introduce a divergent preview mechanism.

#### Scenario: Pattern is consistent across templates

- GIVEN the six affected templates are rendered with their respective file objects present
- WHEN their HTML is compared
- THEN every PDF trigger SHALL use `data-bs-toggle="modal" data-bs-target="#documentPdfModal" data-pdf-url`
- AND every image trigger SHALL use `data-fslightbox="gallery"`

## Coverage Notes

- Triggers are rendered only inside existing `{% if object and object.X %}` guards, so create forms (no file yet) show no trigger and no broken link.
- The in-modal download link of `document_pdf_modal.html` is preserved unchanged.
- Detail pages (`certificate/detail.html`, `publications/detail.html`, `weather_report/_detail.html`, home `avisos`) are out of scope — already correct.
