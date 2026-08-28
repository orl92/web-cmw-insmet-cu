# Tasks: 016-public-ui-ux

## Phase 1: Foundation — shared PDF card + modal

- [x] 1.1 Create `templates/includes/home/document_card.html` (blog card + `<button data-bs-toggle="modal" data-bs-target="#documentPdfModal" data-pdf-url data-pdf-title>`; NO `href="#"`; `summary|sanitize_html`).
- [x] 1.2 Create `templates/includes/home/document_pdf_modal.html` (`modal-xl`, `<object type="application/pdf" data="">` + `<a download>` fallback, `aria-label`, `btn-close` with `aria-label="Cerrar"`).
- [x] 1.3 Create `static/dist/js/document-modal.js` (2-space; on `show.bs.modal` lazy-set `object.data` + `download.href` from `relatedTarget`, only if changed; clear `data` on `hidden.bs.modal`).
- [x] 1.4 Register `document-modal.js` via `{% static %}` in `templates/layouts/avisos.html` and the tiempo/publication templates that render the modal.

## Phase 2: tiempo (WeatherReport)

- [x] 2.1 In `apps/home/templates/pages/home/weather/today.html`: replace inline `pdf_preview.html` + duplicate modal with `document_card.html` + `document_pdf_modal.html` include.
- [x] 2.2 Same change in `tomorrow.html`.
- [x] 2.3 Fix empty-state `alt` in `today.html:59` and `tomorrow.html:59` → `alt="No hay pronósticos"`.

## Phase 3: avisos + valid_until fix

- [x] 3.1 In `templates/layouts/avisos.html`: remove N inline `pdf_preview.html` renders; switch cards to `document_card.html` + single `document_pdf_modal.html`; render `valid_until` ONCE.
- [x] 3.2 In `apps/meteo/forms/warning.py`: replace `valid_until` widget with `forms.DateTimeField(input_formats=['%d/%m/%Y %I:%M %p','%Y-%m-%dT%H:%M','%d/%m/%Y %H:%M'], widget=forms.DateTimeInput(attrs={'class':'form-control'}))`.
- [x] 3.3 In `apps/meteo/models.py`: add `from django.utils import timezone` + `from zoneinfo import ZoneInfo`; add `Warning.save()` that `make_aware(v, ZoneInfo('America/Havana'))` when `v.tzinfo is None`.
- [x] 3.4 Create `apps/meteo/management/commands/normalize_warning_valid_until.py` (`dry_run=True` default, `--apply`, `--reverse`, idempotent, requires DB backup logged at start; touches only naive rows).

## Phase 4: publicaciones (public detail)

- [x] 4.1 In `apps/publications/views.py`: add `ScientificPublicationPublicDetailView(DetailView)` — NO auth/permission mixins; `template_name='pages/publications/public_detail.html'`; `context_object_name='publicacion'`; `get_object` by `uuid`; `select_related('author')`.
- [x] 4.2 In `apps/publications/urls.py`: add `path('<uuid:uuid>/public/', ..., name='public_detail')` (app_name `publications`).
- [x] 4.3 Create `apps/publications/templates/pages/publications/public_detail.html` extending `layouts/home.html`; both "Ver PDF" and "Descargar" → `{{ publicacion.pdf.url }}`.
- [x] 4.4 In `apps/home/templates/pages/home/institution/publications.html`: add "Ver detalle" `<a href="{% url 'publications:public_detail' object.uuid %}">`.

## Phase 5: servicios detail (Service)

- [x] 5.1 In `apps/commercial/models.py`: add `PERIOD_DAYS = 30` class constant on `Service` (no migration).
- [x] 5.2 In `apps/home/templates/pages/home/services/service_detail.html`: `object-fit: cover` → `contain`; render `{{ service.summary|sanitize_html }}`; show `Período estándar: <strong>{{ service.PERIOD_DAYS }} días</strong>`; align layout + related-services/CTA.

## Phase 6: Tests (strict_tdd — MANDATORY)

- [x] 6.1 Create `apps/meteo/tests/test_warning_valid_until.py`: `WarningForm` accepts `05/08/2026 02:30 PM` → aware Havana; `Warning.save()` make_aware naive; mgmt cmd dry-run/no-op/idempotent.
- [x] 6.2 Create `apps/commercial/tests/test_service_detail.py`: `Service.PERIOD_DAYS == 30`; summary sanitized; `object-fit: contain` present in rendered HTML.
- [x] 6.3 Create `apps/home/tests/test_document_card_modal.py`: `document_card.html` renders `<button data-bs-toggle="modal"` (NOT `href="#"`); `data-pdf-url` set; `document_pdf_modal.html` has `<object type="application/pdf">` + `<a download>`.
- [x] 6.4 Create `apps/publications/tests/test_public_detail.py`: anonymous GET `publications:public_detail` → 200 + home layout; both PDF actions == `publicacion.pdf.url`.

## Phase 7: Verify

- [x] 7.1 `python manage.py check`
- [x] 7.2 `python manage.py test apps.meteo apps.home apps.publications apps.commercial`
- [x] 7.3 `djlint . --reformat --check` and `djlint . --lint` on touched templates.
- [x] 7.4 **DB backup prerequisite**: before `normalize_warning_valid_until --apply`, back up the DB; keep `--reverse`/restore path for rollback.

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~520 (partials/JS ~140, meteo form/model/cmd+tests ~160, home templates ~140, publications ~60, commercial ~20) |
| 800-line budget risk | Low |
| Chained PRs recommended | No |
| Delivery strategy | ask-on-risk |
| Decision needed before apply | Yes |
| Chain strategy | pending |
| 400-line budget risk | Low |

**Rationale:** total estimated additions/modifications ≈ 520 lines, well under the 800-line review budget. Changes are cohesive and independent per file; a single PR stays reviewable — no chained PRs. Per `ask-on-risk`, the orchestrator MUST ask the user before `apply`, but the trigger is the DB-changing `normalize_warning_valid_until` command (DB backup required), NOT size.

next_recommended: apply
