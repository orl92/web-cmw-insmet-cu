# Proposal: 016-public-ui-ux

## Intent
Public areas (tiempo/avisos/servicios/publicaciones) have inconsistent PDF UX, a broken `valid_until` save (form rejects the 12h Tempus string; naive rows shift −4/−5h), a staff-gated publication detail, and an a11y alt bug. We unify PDF presentation, fix the date bug at the form+model layer, expose publications publicly, and harden a11y.

## Scope
In: tiempo/WeatherReport, avisos/Warning, servicios/Service detail, publicaciones/ScientificPublication detail, `valid_until` fix + naive-row normalization.
Out: PDF.js full removal (kept as enhancement), API schema changes, new models.

## Capabilities
New: none. Modified: none at spec level (UI/behavior fix within existing capabilities).

## Approach
**Uniform blog-card + native PDF modal.** New `templates/includes/home/document_card.html` (title, summary, author/date, "Ver PDF" `<button data-bs-toggle="modal" data-pdf-url>`) and `templates/includes/home/document_pdf_modal.html` with `<object type="application/pdf">` whose `data` is lazy-set on `show.bs.modal`, plus `<a download>` fallback. Tiny `static/dist/js/document-modal.js` sets `object.data`. Replace inline `pdf_preview.html`/N-renders in avisos & tiempo; drop the double PDF.js modal fetch.

**valid_until (root cause found).** The warning `_form.html:19` ALREADY uses the working `date_field.html`+`fmt_datetime` pattern. The defect is ONLY in `apps/meteo/forms/warning.py`: `valid_until` has no explicit `input_formats`, so it falls to `es`-locale formats lacking the 12h `%I:%M %p` Tempus submits → invalid. Fix mirrors `apps/commercial/forms/subscription.py` exactly:
- `valid_until = forms.DateTimeField(input_formats=['%d/%m/%Y %I:%M %p','%Y-%m-%dT%H:%M','%d/%m/%Y %H:%M'], widget=forms.DateTimeInput(attrs={'class':'form-control'}))`.
- `Warning.save()` adds `make_aware(v, ZoneInfo('America/Havana'))` if `v.tzinfo is None`.
- One-off mgmt command normalizes existing naive rows (DB backup first).

**servicios detail:** `object-fit: contain` (or lightbox); `PERIOD_DAYS = 30` constant on `Service`; `summary|sanitize_html`; Tabler spacing; related-services + CTA.

**publicaciones:** new `ScientificPublicationPublicDetailView` (no auth/permission mixins, `layouts/home.html`); staff CRUD unchanged. Both "Ver PDF" and "Descargar" → `publicacion.pdf.url`.

**tiempo:** empty-state `alt` → "No hay pronósticos".

**a11y:** semantic `header/main/section`, `<button>` modal triggers (no `href="#"`), alt text, AA contrast, not color-only.

## Affected Areas
| Area | Impact |
|---|---|
| `templates/includes/home/{document_card,document_pdf_modal}.html`, `static/dist/js/document-modal.js` | New |
| `templates/layouts/avisos.html`, `apps/home/.../weather/{today,tomorrow}.html` | Modal-only PDF, button triggers, alt fix |
| `apps/meteo/forms/warning.py`, `apps/meteo/models.py:305` | input_formats + make_aware |
| `apps/home/.../services/service_detail.html` | image/period/summary |
| `apps/publications/views.py:263` + new public template | public detail |

## Risks & Rollback
- Naive-row normalization is a data change → **backup DB first**; command idempotent/reversible.
- Rare browsers lack native `<object>` PDF → `<a download>` fallback. Rollback: `git revert` per file; restore DB from backup. Keep `pdf-viewer.js` until enhancement validated.

## Acceptance Criteria (Given/When/Then, RFC 2119)
- GIVEN a warning form, WHEN Tempus submits `05/08/2026 02:30 PM`, THEN it SHALL save `valid_until` aware in `America/Havana` (no −4h shift).
- GIVEN any document area, WHEN user clicks "Ver PDF", THEN a modal SHALL render the PDF via native `<object>` (lazy) with download fallback and SHALL NOT load it twice.
- GIVEN a publication, WHEN an anonymous user opens its public detail, THEN it SHALL render from `layouts/home.html` and both PDF actions SHALL point to `publicacion.pdf.url`.
- GIVEN the tiempo empty state, THEN the alt text SHALL be "No hay pronósticos".
- Modal triggers MUST be `<button>`, never `href="#"`.

## Tests (strict_tdd — MANDATORY)
- `apps.meteo`: `WarningForm` accepts `%d/%m/%Y %I:%M %p`; `Warning.save()` make_aware naive; normalization command.
- `apps.home`/`apps.publications`: templates render card+modal; public detail anonymous-accessible; PDF actions equal `pdf.url`.
- `apps.commercial`: `Service.PERIOD_DAYS` renders 30 días; `summary` sanitized.

## next_recommended
design
