# Tasks: 018-dashboard-file-preview-modal

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~140 (7 templates + ~4 test files, each edit small) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

## Tasks

### Phase 1: Prerequisite — form.html infra

- [x] 1.1 Edit `templates/layouts/form.html`: inside `{% block content %}` after the form `</div>` (before `{% endblock %}`), add `{% include 'includes/home/document_pdf_modal.html' %}`, `<script src="{% static 'dist/js/document-modal.js' %}" defer></script>`, and `<script src="{% static 'dist/libs/fslightbox/index.js' %}" defer></script>`.
- [x]1.2 In the same `{% block content %}` (after the three lines above), add an empty `{% block modal %}{% endblock %}` so orphan modal overrides (e.g. `invoice/create.html`) render. Verify the include/scripts are NOT placed in `{% block extrajs %}`.

### Phase 2: PDF modal triggers (replace target="_blank")

- [x]2.1 `apps/commercial/templates/pages/commercial/service/update.html`: convert the PDF `<a href="{{ object.pdf.url }}" target="_blank">` (lines ~111-119) into `<button type="button" class="btn btn-outline-primary btn-sm" data-bs-toggle="modal" data-bs-target="#documentPdfModal" data-pdf-url="{{ object.pdf.url }}" data-pdf-title="PDF del servicio">…Ver PDF actual</button>`; keep inside `{% if object.pdf %}`.
- [x]2.2 `apps/commercial/templates/pages/commercial/subscription/upload_certificate.html`: convert the PDF `<a href="{{ object.pdf.url }}" target="_blank">` into the same button pattern with `data-pdf-title="Certificado PDF"`; remove `target="_blank"`.
- [x]2.3 `apps/publications/templates/pages/publications/update.html`: convert the PDF `<a href="{{ object.pdf.url }}" target="_blank">` into the same button pattern with `data-pdf-title="Publicación PDF"`; remove `target="_blank"`.
- [x]2.4 `apps/meteo/templates/pages/meteo/warning/_form.html`: convert the PDF `<a href="{{ object.file.url }}" target="_blank">` into the button pattern (`data-pdf-title="Aviso PDF"`) guarded by `{% if object and object.file %}`; remove `target="_blank"`.
- [x]2.5 `apps/meteo/templates/pages/meteo/weather_report/_form.html`: convert the PDF `<a href="{{ object.file.url }}" target="_blank">` into the button pattern (`data-pdf-title="Reporte meteorológico PDF"`) guarded by `{% if object and object.file %}`; remove `target="_blank"`.

### Phase 3: Image fslightbox triggers (replace target="_blank" / add)

- [x]3.1 `apps/commercial/templates/pages/commercial/service/update.html`: convert the image `<a href="{{ object.get_image_url }}" target="_blank">` (lines ~157-165) into `<a class="btn btn-outline-primary btn-sm" data-fslightbox="gallery" href="{{ object.get_image_url }}">…Ver imagen actual</a>` inside `{% if object.image %}`; remove `target="_blank"`.
- [x]3.2 `apps/user_auth/templates/pages/user_auth/profile/update.html`: inside `{% if request.user.profile.avatar %}`, add next to "Eliminar" a `<a class="btn btn-outline-primary btn-sm" data-fslightbox="gallery" href="{{ request.user.profile.get_avatar }}">Ver imagen actual</a>`; keep the existing delete submit button.

### Phase 4: Tests (strict_tdd)

- [x]4.1 `apps/commercial` test: login superuser, create a `Service` with `pdf` + `image`, GET `service:update`; assert `b'target="_blank"'` NOT in response, `b'data-pdf-url='` present, `b'data-fslightbox'` present, `b'documentPdfModal'` present.
- [x]4.2 `apps.publications` test: create a publication with `pdf`, GET update; assert no `target="_blank"`, `data-pdf-url=` present, `documentPdfModal` present.
- [x]4.3 `apps.meteo` test: create a `Warning` with `file` and a `WeatherReport` with `file`, GET each update/create; assert no `target="_blank"`, `data-pdf-url=` present, `documentPdfModal` present.
- [x]4.4 `apps.user_auth` test: login superuser with a `Profile` having `avatar`, GET profile update; assert `data-fslightbox` present, `documentPdfModal` present, no `target="_blank"`.
- [x]4.5 Confirm the create-form path (no file) shows NO `data-pdf-url`/`data-fslightbox` when object/file absent.

### Phase 5: Verification

- [x]5.1 Run `python manage.py check` — must be clean.
- [x]5.2 Run `djlint . --reformat --check` — must pass on changed templates.
- [x]5.3 Run `python manage.py test apps.commercial apps.publications apps.meteo apps.user_auth` — all green.
