# Proposal: 018-dashboard-file-preview-modal

## Intent

Today, several dashboard **edit/update** templates open uploaded files directly in a blank browser tab via `<a href="...url" target="_blank">`. That breaks UI consistency: some pages (home `avisos`, detail views) already use the shared PDF modal and the vendored `fslightbox` image lightbox, while form pages bypass them.

**Goal:** in every edit/create form where a PDF or image file field exists, the "Ver PDF" button opens the shared `#documentPdfModal` and the "Ver imagen" button opens `fslightbox`. No file is ever opened in a new browser tab. This unifies the preview integration project-wide and reuses existing, already-vendored assets (no new libraries).

## Scope

### In Scope
- **Prerequisite fix** `templates/layouts/form.html`: re-expose `{% block modal %}` (currently dropped because `form.html` overrides `content` wholesale) and load the shared preview infra once (PDF modal include + `document-modal.js` + `fslightbox/index.js`) so all form pages get it.
- Migrate these 6 templates (replace `target="_blank"` raw-file links with modal/lightbox triggers):
  1. `apps/commercial/.../service/update.html` — PDF (`object.pdf.url`) + image (`object.get_image_url`)
  2. `apps/commercial/.../subscription/upload_certificate.html` — PDF (`object.pdf.url`)
  3. `apps/publications/.../update.html` — PDF (`object.pdf.url`)
  4. `apps/meteo/.../warning/_form.html` (early_warning/storm/tropical_cyclone create+update) — PDF (`object.file.url`)
  5. `apps/meteo/.../weather_report/_form.html` (today/tomorrow/commentary create+update) — PDF (`object.file.url`)
  6. `apps/user_auth/.../profile/update.html` — avatar: **add** a "Ver imagen" `fslightbox` button (href `request.user.profile.get_avatar`); currently shows thumbnail + "Eliminar" only.

### Out of Scope
- Detail pages (`commercial/certificate/detail.html`, `publications/detail.html`, `meteo/weather_report/_detail.html`, home `avisos`) — already correct.
- New libraries, API changes, model changes, migrations.

## Capabilities

### New Capabilities
None — pure presentation-layer consistency; no spec-level behavior change.

### Modified Capabilities
None — no `openspec/specs/` requirement deltas. The consistency rule is enforced via templates + tests, not a capability spec.

## Approach

- **PDF:** reuse `templates/includes/home/document_pdf_modal.html` (modal `#documentPdfModal`, `<object data=...>` + download link) and `static/dist/js/document-modal.js`. Convert each PDF link into a trigger button:
  `<button type="button" data-bs-toggle="modal" data-bs-target="#documentPdfModal" data-pdf-url="{{ object.X.url }}" data-pdf-title="...">Ver PDF</button>` (drop `target="_blank"`).
- **Image:** reuse vendored `static/dist/libs/fslightbox/index.js` (auto-scans `[data-fslightbox]` on load). Convert each image link into `<a data-fslightbox="gallery" href="{{ image_url }}" class="btn ...">Ver imagen</a>`.
- **form.html prerequisite (critical):** add `{% block modal %}{% include 'includes/home/document_pdf_modal.html' %} <script ...document-modal.js></script> <script ...fslightbox/index.js defer></script> {% endblock %}` inside `{% block content %}`. The scripts MUST live here, **not** in `{% block extrajs %}` of `form.html`, because `service/update.html` and `publications/update.html` override `{% block extrajs %}` without `{{ block.super }}` and would drop them. Anchors are server-rendered static HTML, so fslightbox picks them up on load (no dynamic-injection concern).
- Keep the in-modal download link intact.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `templates/layouts/form.html` | Modified | Re-expose modal block + load shared preview infra |
| 6 listed form templates | Modified | Links → modal/lightbox triggers; remove `target="_blank"` |
| `static/dist/js/document-modal.js`, `fslightbox/index.js` | Reused | No changes |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Child `extrajs` override drops modal scripts | Med | Scripts placed in `{% block modal %}` within `content`, not `extrajs` |
| `object.file`/`object.pdf`/`get_avatar` None on create | Low | Trigger button only rendered inside existing `{% if object and object.X %}` block |
| fslightbox not initialized for static anchors | Low | Vendored script auto-scans on load; anchors present at parse time |

## Rollback Plan

Revert the 7 template changes via git (`git checkout -- <files>` + `templates/layouts/form.html`). No DB/migration impact.

## Dependencies

- Existing: `includes/home/document_pdf_modal.html`, `static/dist/js/document-modal.js`, `static/dist/libs/fslightbox/index.js` (all present, no new vendor).

## Success Criteria

- [ ] Every "Ver PDF" button on the 6 templates opens `#documentPdfModal` showing the file; no `target="_blank"` to a file URL remains.
- [ ] Every image preview (service image, profile avatar) opens `fslightbox`; no `target="_blank"` to an image URL remains.
- [ ] `form.html` exposes the modal and loads both scripts on all form pages.
- [ ] `python manage.py test apps.<app>` passes (new/extended tests assert absence of `target="_blank"` for file URLs and presence of `data-pdf-url`/`data-fslightbox`/ `documentPdfModal`).

## Testing (strict_tdd = true)

Add/extend a test per affected app that renders the update view (authenticated superuser + created object) and asserts:
- `b'target="_blank"'` **not** in `response.content` for file URLs;
- `b'data-pdf-url='` present where a PDF exists;
- `b'data-fslightbox'` present where an image exists;
- `b'documentPdfModal'` present (proves `form.html` now includes the modal).
Run with `python manage.py test apps.commercial apps.publications apps.meteo apps.user_auth`.
