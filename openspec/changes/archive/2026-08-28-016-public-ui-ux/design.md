# Design: 016-public-ui-ux

## Technical Approach
Unify PDF presentation across tiempo/avisos/publicaciones with two shared partials
(`document_card.html` + `document_pdf_modal.html`) driven by a tiny `document-modal.js`
that lazy-sets `<object data>` on `show.bs.modal` (no double-fetch). Fix `valid_until`
at the form+model layer (explicit `input_formats` + `make_aware` safeguard + one-off
normalization command). Expose a public `ScientificPublication` detail. Tighten a11y.

## Architecture Decisions (with rationale)

| # | Decision | Options | Rationale |
|---|----------|---------|-----------|
| 1 | Native `<object>` modal for tiempo/avisos/publicaciones | A native `<object>` (chosen); B keep PDF.js lazy; C hybrid | Lightest, accessible, zero JS for common case; target browsers have built-in viewers; `<a download>` fallback covers rare cases. |
| 2 | **KEEP** `pdf_preview.html`/`pdf_modal.html`/`pdf-viewer.js`/`pdf.min.js` | Remove (proposal) vs Keep (chosen) | Used by out-of-scope areas (commentaries, services public/commercial, publications list) AND asserted by `apps/home/tests/test_pdf_viewer_a11y.py`. Removing breaks them. Scope is only tiempo/avisos/servicios/publicaciones. |
| 3 | `valid_until` fix = explicit `input_formats` + `make_aware` + mgmt cmd | A (chosen); B Tempus→ISO; C FORMAT_MODULE_PATH | Localized, unit-testable in `apps.meteo`; avoids global datetime-format risk. |
| 4 | Public publication detail = new un-gated `DetailView` on `layouts/home.html`; staff CRUD untouched | A (chosen); B keep gated | Public portal must expose read views without login. |
| 5 | `PERIOD_DAYS = 30` as `Service` class constant | Constant (chosen) vs computed from dates | Business rule, no start/end fields on Service; constant avoids magic number. |

## Data Flow
Card `<button data-pdf-url>` → Bootstrap `show.bs.modal` → `document-modal.js` reads
`data-pdf-url`/`data-pdf-title`, sets `<object data>` (+ `<a download href>`),
sets title. `hidden.bs.modal` clears `data` to free memory. No preview fetch on list.

## New Partials / JS (skeletons, 2-space, Tabler)

`templates/includes/home/document_card.html`:
```html
<article class="card">
  <div class="card-body">
    {% if badge %}<span class="badge bg-primary mb-2">{{ badge }}</span>{% endif %}
    <h3 class="card-title">{{ title }}</h3>
    {% if summary %}<p class="text-secondary">{{ summary|sanitize_html }}</p>{% endif %}
    <div class="list-inline list-inline-dots text-secondary mb-3">
      {% if publisher %}<span class="list-inline-item"><i class="icon ti ti-user"></i> {{ publisher }}</span>{% endif %}
      {% if date %}<span class="list-inline-item"><i class="icon ti ti-calendar-time"></i> {{ date }}</span>{% endif %}
    </div>
    {% if pdf_url %}
    <button type="button" class="btn btn-pill btn-outline-primary"
            data-bs-toggle="modal" data-bs-target="#documentPdfModal"
            data-pdf-url="{{ pdf_url }}" data-pdf-title="{{ pdf_title|default:title }}">
      <i class="icon ti ti-file-type-pdf"></i> Ver PDF
    </button>
    {% endif %}
  </div>
</article>
```

`templates/includes/home/document_pdf_modal.html` (modal-xl):
```html
<div class="modal modal-xl fade" id="documentPdfModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered modal-xl">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="documentPdfModalLabel">Documento</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
      </div>
      <div class="modal-body">
        <object id="documentPdfObject" type="application/pdf" data="" aria-label="Vista previa del PDF" style="width:100%;height:80vh;">
          <a id="documentPdfDownload" href="#" download class="btn btn-primary"><i class="icon ti ti-download"></i> Descargar PDF</a>
        </object>
      </div>
    </div>
  </div>
</div>
```

`static/dist/js/document-modal.js`:
```js
document.addEventListener('DOMContentLoaded', function () {
  var modal = document.getElementById('documentPdfModal');
  if (!modal) return;
  modal.addEventListener('show.bs.modal', function (e) {
    var t = e.relatedTarget;
    var url = t.getAttribute('data-pdf-url');
    var title = t.getAttribute('data-pdf-title') || 'Documento';
    var obj = document.getElementById('documentPdfObject');
    document.getElementById('documentPdfModalLabel').textContent = title;
    document.getElementById('documentPdfDownload').href = url;
    if (obj.getAttribute('data') !== url) obj.setAttribute('data', url); // no double-fetch
  });
  modal.addEventListener('hidden.bs.modal', function () {
    document.getElementById('documentPdfObject').setAttribute('data', '');
  });
});
```

## valid_until Fix (exact)
**Form** (`apps/meteo/forms/warning.py`): replace `valid_until` widget with explicit field:
```python
valid_until = forms.DateTimeField(
    input_formats=['%d/%m/%Y %I:%M %p', '%Y-%m-%dT%H:%M', '%d/%m/%Y %H:%M'],
    widget=forms.DateTimeInput(attrs={'class': 'form-control'}),
)
```
(Exact list copied from `SubscriptionForm.start_date/end_date`.)

**Model** (`apps/meteo/models.py`): add `Warning.save()` safeguard (import `from django.utils import timezone` + `from zoneinfo import ZoneInfo`):
```python
def save(self, *args, **kwargs):
    if self.valid_until and self.valid_until.tzinfo is None:
        self.valid_until = timezone.make_aware(self.valid_until, ZoneInfo('America/Havana'))
    super().save(*args, **kwargs)
```

**Mgmt command** `apps/meteo/management/commands/normalize_warning_valid_until.py`:
- `handle(self, *args, **options)` with `dry_run=True` default (`--apply` to write).
- Queryset `Warning.objects.filter(valid_until__isnull=False)`; for each, if `valid_until.tzinfo is None` → `make_aware(..., ZoneInfo('America/Havana'))`.
- Idempotent (only naive rows touched; re-run no-ops). Lossless (wall-clock preserved).
- Reversible: restore DB from backup; optional `--reverse` strips tzinfo for emergency rollback.
- Prints count; **requires DB backup first** (logged at start).

## publicaciones Detail (new)
- View: `class ScientificPublicationPublicDetailView(DetailView)` — **no** `LoginRequiredMixin`/`PermissionRequiredMixin`; `template_name='pages/publications/public_detail.html'`; `context_object_name='publicacion'`; `get_object` by `uuid`; `select_related('author')`.
- URL: add `path('<uuid:uuid>/public/', ScientificPublicationPublicDetailView.as_view(), name='public_detail')` (app_name `publications`).
- Template extends `layouts/home.html`; both "Ver PDF" and "Descargar" → `{{ publicacion.pdf.url }}`.
- Existing `ScientificPublicationDetailView` (gated) + `pdf/` stay unchanged.
- List (`institution/publications.html`) gains a "Ver detalle" `<a href="{% url 'publications:public_detail' object.uuid %}">`.

## servicios Detail
- `Service.PERIOD_DAYS = 30` class constant (no migration; constant only).
- Template: `object-fit: cover` → `contain`; render `{{ service.summary|sanitize_html }}`; `Período estándar: <strong>{{ service.PERIOD_DAYS }} días</strong>`; related-services + CTA block.

## tiempo
- `today.html:59` & `tomorrow.html:59`: `alt="No hay publicaciones"` → `alt="No hay pronósticos"`.

## File Changes
| File | Action | Description |
|------|--------|-------------|
| `templates/includes/home/document_card.html` | Create | Shared blog card + PDF trigger button |
| `templates/includes/home/document_pdf_modal.html` | Create | Native `<object>` modal-xl |
| `static/dist/js/document-modal.js` | Create | Lazy-set object data |
| `apps/meteo/forms/warning.py` | Modify | explicit `input_formats` |
| `apps/meteo/models.py` | Modify | `Warning.save()` make_aware + imports |
| `apps/meteo/management/commands/normalize_warning_valid_until.py` | Create | normalize naive rows |
| `apps/publications/views.py` | Modify | add public detail view |
| `apps/publications/urls.py` | Modify | add `public_detail` path |
| `apps/publications/templates/pages/publications/public_detail.html` | Create | public template |
| `apps/home/.../institution/publications.html` | Modify | add "Ver detalle" link |
| `apps/home/.../weather/{today,tomorrow}.html` | Modify | use card/modal + alt fix |
| `templates/layouts/avisos.html` | Modify | replace N previews + modal with card/modal |
| `apps/home/.../services/service_detail.html` | Modify | image/period/summary |

KEEP (do NOT delete): `pdf_preview.html`, `pdf_modal.html`, `pdf-viewer.js`, `pdf.min.js`, `test_pdf_viewer_a11y.py`.

## Threat Matrix
N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary in this change.

## Migration / Rollback
- No model migration (PERIOD_DAYS constant only; Warning.save is behavior).
- `normalize_warning_valid_until` is a data change → **backup DB first**; idempotent; rollback = restore backup (or `--reverse`).
- Rollback code: `git revert` per file.

## Testing Strategy (strict_tdd)
| Layer | What | Approach |
|-------|------|----------|
| Unit (apps.meteo) | `WarningForm` accepts `05/08/2026 02:30 PM` → aware Havana; `Warning.save()` make_aware naive; mgmt cmd dry-run/no-op/idempotent | `apps/meteo/tests/test_warning_valid_until.py` |
| Unit (apps.commercial) | `Service.PERIOD_DAYS == 30`; summary sanitized; `object-fit: contain` in render | `apps/commercial/tests/test_service_detail.py` |
| Unit (apps.home) | `document_card.html` has `<button data-bs-toggle="modal"` (NOT `href="#"`), `data-pdf-url`; `document_pdf_modal.html` has `<object type="application/pdf">` + `<a download>` | `apps/home/tests/test_document_card_modal.py` |
| Unit (apps.publications) | anonymous GET `publications:public_detail` → 200 + home layout; both PDF actions == `pdf.url` | `apps/publications/tests/test_public_detail.py` |

Per-app: `python manage.py test apps.meteo|apps.home|apps.publications|apps.commercial`.

## Open Questions
- None blocking (user approved direction). Deviation: kept shared PDF.js partials (decision #2) — needs orchestrator sign-off.
