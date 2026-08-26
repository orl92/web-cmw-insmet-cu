# Design: 018-dashboard-file-preview-modal

## Technical Approach

Unify file preview on every dashboard form page by reusing the already-vendored
PDF modal (`includes/home/document_pdf_modal.html` + `document-modal.js`) and the
vendored `fslightbox` image lightbox. No new libraries, no model/migration change.
The only risk is that the shared preview infra must survive child-template block
overrides; the design hardcodes it inside `form.html`'s `{% block content %}` so no
child `{% block extrajs %}` or `{% block modal %}` override can drop it.

## Architecture Decisions

| Decision | Options considered | Choice | Rationale |
|---|---|---|---|
| Where to load shared preview infra | (a) hardcode include+scripts in `form.html` `content`; (b) re-expose `{% block modal %}` and put them there | **(a)** hardcode in `content` | Child `service/update.html` & `publications/update.html` override `{% block extrajs %}` without `{{ block.super }}`; `invoice/create.html` overrides `{% block modal %}` without `block.super`. Both would drop option (b). Hardcoding in `content` is immune to any block override. |
| Also re-expose `{% block modal %}`? | yes / no | **yes (empty)** | `invoice/create.html` already defines `{% block modal %}` that is currently orphaned (form.html never declared it). Re-exposing it fixes that latent bug and lets page-specific modals render; the shared PDF modal stays in `content`, so no id collision. |
| Where to load fslightbox | `form.html` vs `dashboard.html` | **`form.html`** | Every form page extends `form.html`; `dashboard.html` is for list/detail. Loading in `form.html` guarantees every form page (this change's scope) has fslightbox. Anchors are server-rendered, so fslightbox auto-scans them on load. |
| Profile image guard | `{% if request.user.profile.avatar %}` vs always | **guard with `avatar`** | `get_avatar()` always returns a URL (default `dist/img/avatar.png`), but "Ver imagen actual" only makes sense when a real avatar exists; matches the `{% if object.image %}` pattern used elsewhere. |

## Data Flow

```
form.html (content, always present)
 ├─ {% include 'includes/home/document_pdf_modal.html' %}  → #documentPdfModal markup
 ├─ <script document-modal.js defer>   → wires data-pdf-url triggers on show.bs.modal
 └─ <script fslightbox/index.js defer> → auto-scans [data-fslightbox] anchors

Child template
 ├─ PDF link  → <button data-bs-toggle=modal data-bs-target=#documentPdfModal
 │             data-pdf-url=... data-pdf-title=...>  (NO href, NO target=_blank)
 └─ Image link → <a data-fslightbox="gallery" href=...>  (NO target=_blank)
```

## Prerequisite Fix — `templates/layouts/form.html`

Inside the existing `{% block content %} … {% endblock %}` (after the form `</div>`,
before `{% endblock %}`), add:

```django
  {% include 'includes/home/document_pdf_modal.html' %}
  <script src="{% static 'dist/js/document-modal.js' %}" defer></script>
  <script src="{% static 'dist/libs/fslightbox/index.js' %}" defer></script>
  {% block modal %}{% endblock %}
```

`form.html` already has `{% load static %}` (line 2). This satisfies REQ-003: modal
markup + both scripts present on every form page, and never in `extrajs`.

## Per-Template Button Transformations

### 1. `apps/commercial/.../service/update.html` (PDF `object.pdf.url` + image `object.get_image_url`)

PDF — BEFORE (lines 111-119):
```django
            {% if object.pdf %}
              <div class="mt-2">
                <a href="{{ object.pdf.url }}" target="_blank" class="btn btn-outline-primary btn-sm">
                  <i class="icon ti ti-download"></i> Ver PDF actual
                </a>
              </div>
            {% endif %}
```
AFTER:
```django
            {% if object.pdf %}
              <div class="mt-2">
                <button type="button" class="btn btn-outline-primary btn-sm"
                        data-bs-toggle="modal" data-bs-target="#documentPdfModal"
                        data-pdf-url="{{ object.pdf.url }}" data-pdf-title="PDF del servicio">
                  <i class="icon ti ti-download"></i> Ver PDF actual
                </button>
              </div>
            {% endif %}
```
Image — BEFORE (lines 157-165) `target="_blank"` `<a href="{{ object.get_image_url }}">`;
AFTER:
```django
            {% if object.image %}
              <div class="mt-2">
                <a class="btn btn-outline-primary btn-sm" data-fslightbox="gallery"
                   href="{{ object.get_image_url }}">
                  <i class="icon ti ti-eye"></i> Ver imagen actual
                </a>
              </div>
            {% endif %}
```

### 2. `apps/commercial/.../subscription/upload_certificate.html` (PDF `object.pdf.url`)

BEFORE (lines 38-47) `<a href="{{ object.pdf.url }}" target="_blank" …>Ver PDF actual</a>`;
AFTER (same button pattern, `data-pdf-title="Certificado PDF"`):
```django
  {% if object.pdf %}
    <div class="mt-2">
      <button type="button" class="btn btn-outline-primary btn-sm"
              data-bs-toggle="modal" data-bs-target="#documentPdfModal"
              data-pdf-url="{{ object.pdf.url }}" data-pdf-title="Certificado PDF">
        <i class="icon ti ti-download"></i> Ver PDF actual
      </button>
    </div>
  {% endif %}
```

### 3. `apps/publications/.../update.html` (PDF `object.pdf.url`)

BEFORE (lines 273-281) `<a href="{{ object.pdf.url }}" target="_blank" …>Ver PDF actual</a>`;
AFTER: identical button pattern, `data-pdf-title="Publicación PDF"`.

### 4. `apps/meteo/.../warning/_form.html` (PDF `object.file.url`)

BEFORE (lines 43-52) `<a href="{{ object.file.url }}" target="_blank" …>Ver PDF</a>`;
AFTER:
```django
{% if object and object.file %}
  <div class="mt-3">
    <button type="button" class="btn btn-outline-primary btn-sm"
            data-bs-toggle="modal" data-bs-target="#documentPdfModal"
            data-pdf-url="{{ object.file.url }}" data-pdf-title="Aviso PDF">
      <i class="icon ti ti-eye"></i> Ver PDF
    </button>
  </div>
{% endif %}
```

### 5. `apps/meteo/.../weather_report/_form.html` (PDF `object.file.url`)

BEFORE (lines 38-47) same `object.file.url` `<a target="_blank">Ver PDF</a>`;
AFTER: identical button pattern, `data-pdf-title="Reporte meteorológico PDF"`.

### 6. `apps/user_auth/.../profile/update.html` (avatar image — ADD fslightbox)

BEFORE (lines 135-144) only the "Eliminar" submit button inside
`{% if request.user.profile.avatar %}`. AFTER (add "Ver imagen actual" anchor next to it):
```django
              {% if request.user.profile.avatar %}
                <div class="mt-2 d-flex gap-2">
                  <a class="btn btn-outline-primary btn-sm" data-fslightbox="gallery"
                     href="{{ request.user.profile.get_avatar }}">
                    <i class="icon ti ti-eye"></i> Ver imagen actual
                  </a>
                  <button type="submit" name="delete_avatar" class="btn btn-outline-danger btn-sm">
                    <i class="icon ti ti-trash"></i> Eliminar
                  </button>
                </div>
              {% endif %}
```
`Profile.get_avatar()` (models.py:41) returns `avatar.url` or a default PNG, always a
valid URL — safe as fslightbox `href`.

## Interfaces / Contracts

- `document-modal.js` reads `data-pdf-url` + `data-pdf-title` from the trigger
  (`e.relatedTarget`) and sets `#documentPdfObject` `data` and `#documentPdfDownload`
  `href`. **No change required** — keep the in-modal download link intact.
- fslightbox auto-initializes any `[data-fslightbox]` anchor on script load.

## Testing Strategy (strict_tdd)

| Layer | What to Test | Approach |
|---|---|---|
| Unit/View | Each affected update view renders with trigger, no `_blank` | Per-app Django `TestCase`: login superuser, create object with file, GET the update URL; assert `b'target="_blank"'` NOT in `response.content`; `b'data-pdf-url='` present (pdf templates); `b'data-fslightbox'` present (image templates); `b'documentPdfModal'` present (form.html includes modal) |
| View | Create form (no file) shows no broken trigger | Assert no `data-pdf-url`/`data-fslightbox` when object/file absent |

Run: `python manage.py test apps.commercial apps.publications apps.meteo apps.user_auth`.

## Migration / Rollout

No migration. Pure template change. Rollback: `git checkout -- <7 files>`.

## Open Questions

- None blocking. Should the profile fslightbox also cover the default placeholder
  (unguarded)? Decided: guard with `avatar` for label correctness.
