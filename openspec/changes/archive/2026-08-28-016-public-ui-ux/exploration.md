# Exploration: 016-public-ui-ux

> Scope: 4 public-facing template areas + 1 date/time bug. Django **5.1.4 (pinned)** — do NOT assume 5.2 APIs.
> Mode: interactive. No code was changed. Findings verified by reading real code + a live Django-shell reproduction.

## Current State (verified)

### 1. Home "tiempo" (WeatherReport) — PDF viewing
- `apps/home/templates/pages/home/weather/today.html` and `tomorrow.html` each:
  - Render an **inline PDF.js preview** via `includes/home/pdf_preview.html` (lines 24‑26 today / equivalent tomorrow) **and** a "Ver PDF" modal trigger (lines 36‑47) that loads the **same** `pdf_url` again.
  - Use `{{ weather_today.summary|sanitize_html }}` (today.html:28) — good.
  - **BUG (a11y):** empty-state image `alt="No hay publicaciones"` (today.html:59, tomorrow.html:59) is wrong — these are weather pages; should read "No hay pronósticos". The `<p>` subtitle is correct ("pronosticos para hoy/mañana").
  - No native `<object>`/fallback if PDF.js fails.

### 2. "avisos" / warnings (Warning) — PDF listing + valid_until bug
- `templates/layouts/avisos.html` is the single shared layout (the three `warnings/*.html` only `{% extends %}` it — confirmed 1 line each).
- Renders **N inline PDF.js previews simultaneously** (one per warning, `pdf_preview.html` loop at lines 32‑36) **plus** a modal that re-fetches the PDF → PDF loaded **twice**.
- `valid_until` rendered at **avisos.html:19** (`|date:'j \d\e F \d\e Y'`), **:22** (`|time:'h:i A'`), **:44** (`|date:'d/m/Y h:i A'`) — three redundant renderings.

### 3. "servicios" detail (Service, commercial) — UX
- `apps/home/templates/pages/home/services/service_detail.html`:
  - Image `object-fit: cover` with `max-height:300px` (lines 9‑13) crops the image.
  - "Período estándar: **30 días**" is **hardcoded** (line 26). `Service` model has **no** period/duration field (`apps/commercial/models.py:86` — fields: summary `CharField(500)`, service_type, image, price, pdf). It is a business constant, not from the model.
  - `{{ service.summary }}` is rendered **raw** (line 44) — no `|linebreaks`/`|sanitize_html` (unlike weather). Inconsistent; minor XSS-surface even if staff-authored.
  - **Verified FALSE:** the prior claim that `#transfer-info` had two `class` attributes is wrong — service_detail.html:93‑95 is one `id`, one `style`, one `class` (valid HTML). Not a bug.
  - Uneven whitespace between blocks (uses inline `style` + `mb-*` inconsistently).

### 4. "publicaciones" (ScientificPublication) — PDF detail
- `apps/publications/templates/pages/publications/detail.html:1` **extends `layouts/dashboard.html`** (staff-only) and `ScientificPublicationDetailView` is gated by `LoginRequiredMixin` + `PermissionRequiredMixin` (`apps/publications/views.py:263`).
  - **This is wrong for a PUBLIC publication.** A public portal should expose a public detail view/template (extend `layouts/home.html`, no auth gate). Currently the public only sees the list+modal (`apps/home/templates/pages/home/institution/publications.html`) which offers "Ver PDF" (uploaded file) and there is **no public detail link**.
- Confirmed asymmetry: "Ver PDF" (uploaded file) vs "Descargar" (regenerated xhtml2pdf summary) are **different documents** — must be labeled distinctly.

### 5. PDF viewer architecture (shared by 1, 2, 4)
- `static/dist/js/pdf-viewer.js:427‑444` `initializeAll()` builds a preview viewer for the main container **and** for every `[id^="pdfPreviewContainer-"]`, AND the modal (`lines 400‑408`) re-fetches `data-pdf-url` into `modalPdfPages`. So the same PDF is fetched **twice** (preview + modal), and avisos fires **N simultaneous** PDF.js renders.
- PDF.js libs vendored in `static/dist/libs/PDF/` (offline-friendly, no build) — keep available as progressive enhancement, but the default path is heavy.

## valid_until — Root Cause (precise)

**Model:** `Warning.valid_until = models.DateTimeField(verbose_name='Válido hasta')` (`apps/meteo/models.py:305`). `USE_TZ=True`, `TIME_ZONE='America/Havana'` (`config/settings.py:249‑251`). Field type is correct.

**Display:** `templates/layouts/avisos.html:19, 22, 44` use Django's built-in `date`/`time` filters. These localize correctly **for timezone-aware** values — proven in a shell: an aware `America/Havana` value renders `5 de Agosto de 2026` / `02:30 PM`.

**The shift (proven):** when `valid_until` is stored **naive**, Django's DB layer treats it as **UTC** on save; the template then re-localizes UTC→Havana, producing a **−4/−5h** shift (intended 14:30 → shown 10:30 AM), and a **day-boundary shift** near midnight. The 088 "fix" (commit `dd8926e`) only swapped format strings (`H:i`→`h:i A`) and did **not** enforce awareness, so the symptom persists for any naive-stored row.

**Deeper, current blocker (discovered):** `WarningForm.valid_until` **rejects** the 12h `dd/MM/yyyy hh:mm AM/PM` string that Tempus Dominus actually submits (`date_field.html` + `tempus-init.js:canonicalFormat`). The field's `input_formats` resolves to Django's **built-in `es` locale** `DATETIME_INPUT_FORMATS` (24h `%H:%M`), which **shadows** the project `DATETIME_INPUT_FORMATS` setting (that does include `%I:%M %p`, settings.py:261). Only ISO `%Y-%m-%dT%H:%M` is accepted. Proven: `clean('05/08/2026 02:30 PM')` → invalid; `clean('2026-08-05T14:30')` → aware Havana. **Consequence:** the create/edit form fails validation on `valid_until`, so warnings cannot be saved through the UI — any displayed warnings come from API/legacy paths, which is exactly where the shifted times originate.

**Precise fix location:** the bug is **not** in the template lines but in the **form/storage layer**:
- `apps/meteo/forms/warning.py` — set explicit `input_formats` on the `valid_until` field so the 12h string parses (bypasses the `es`-locale shadow; robust to `LANGUAGE_CODE`).
- `apps/meteo/models.py:305` — add a defensive `save()`/`clean()` that `make_aware(..., ZoneInfo('America/Havana'))` any naive `valid_until`, plus a one-off normalization of existing naive rows.
- Template: keep `date`/`time` filters (correct for aware data) and consolidate the 3 renderings into one consistent format.

## Approaches Compared

### PDF viewing (areas 1, 2, 4)
- **A — Native `<object type="application/pdf">` (RECOMMENDED):** browser-native zoom/print/download, zero JS for the common case. Lazy-set `data` in a `modal-xl` on `show.bs.modal` (read `data-pdf-url` from the trigger). Eliminates double-load and the N-simultaneous avisos renders. Provide `<a download>` fallback inside `<object>` for no-JS/unsupported viewers.
  - *Pros:* lightest, most accessible, no PDF.js maintenance. *Cons:* relies on the browser's built-in PDF viewer (Chrome/Edge/Firefox OK — the target audience).
- **B — Keep PDF.js but lazy:** render preview only via `IntersectionObserver`/`show.bs.modal`, reuse a single modal instance. Keeps guaranteed rendering but retains PDF.js weight/complexity.
- **C — Hybrid:** native `<object>` primary; if `!navigator.pdfViewerEnabled`, enhance with PDF.js. More code, safest coverage.

### valid_until fix
- **A — Explicit `input_formats` on form field + model `make_aware` safeguard (RECOMMENDED):** small, localized, unit-testable (`apps.meteo` label). Fixes both the save-blocker and the shift.
- **B — Make Tempus submit ISO:** change `canonicalFormat` to `%Y-%m-%dT%H:%M` to match the widget `format`. More churn (initial value + parsing + display all shift to ISO).
- **C — `FORMAT_MODULE_PATH` custom es module:** restores the settings `%I:%M %p` globally. Broadest impact, riskier (affects all datetime inputs).

### servicios detail
- Fix image (`object-fit: cover` + aspect-ratio container, or `contain`), derive "30 días" from a `PERIOD_DAYS` constant in context, apply `|linebreaks`/`|sanitize_html` to `summary`, normalize spacing with Tabler utilities.

### publicaciones detail
- **A — New public detail view + template** (`layouts/home.html`, no auth/permission mixins), reachable from the list. Keep staff CRUD gated. **RECOMMENDED.**
- **B — Leave dashboard-gated:** not acceptable for a public portal.

## Affected Areas (files)
- `templates/layouts/avisos.html` — valid_until (19/22/44), N inline previews, double-load.
- `apps/home/templates/pages/home/weather/{today,tomorrow}.html` — wrong `alt` (59), double-load.
- `apps/home/templates/pages/home/services/service_detail.html` — image crop (9‑13), hardcoded 30 días (26), raw summary (44).
- `apps/publications/templates/pages/publications/detail.html` + `apps/publications/views.py:263` — staff-only layout/gating (wrong for public).
- `apps/meteo/forms/warning.py`, `apps/meteo/models.py:305` — valid_until storage/locale blocker.
- `static/dist/js/pdf-viewer.js:427‑444` — double-load / N previews.
- `templates/includes/home/{pdf_preview,pdf_modal}.html` — replaced/kept per chosen approach.

## Recommendation
1. Adopt **native `<object>` PDF viewer (Approach A)** for tiempo/avisos/publicaciones, modal-xl, lazy `data`, with `<a download>` fallback. Remove inline N-previews in avisos (modal-only) and the duplicate modal fetch.
2. Fix **valid_until** at the form+model layer (Approach A): explicit `input_formats` + `make_aware` safeguard + normalize existing rows. Keep `date`/`time` filters in template; consolidate the 3 renderings.
3. Create a **public** ScientificPublication detail (layout `home`, no auth gate); keep staff CRUD.
4. servicios detail: image `object-fit` fix, `PERIOD_DAYS` constant, `|sanitize_html`/`|linebreaks` on summary, spacing cleanup.
5. Fix weather empty-state `alt` text.

## Risks
- Native `<object>` depends on the browser's built-in PDF viewer; extremely rare environments lack one → mitigated by `<a download>` fallback.
- Changing `input_formats` must keep `DATETIME_INPUT_FORMATS` compatible for other datetime fields; scope the explicit formats to the `valid_until` field only.
- Normalizing existing naive `valid_until` rows is a data change — needs a one-off management command / data migration and a backup.
- `href="#"` modal triggers (avisos/tiempo/publications) cause focus jump to top on activate — use `<button>` for keyboard correctness (a11y).

## Open Questions for the User
1. Publicaciones detail: fully public (no login) for read, or public-read but PDF download gated to logged-in?
2. valid_until fix scope: confirm **Approach A** (explicit `input_formats` + `make_aware` safeguard + normalize rows) vs the broader `FORMAT_MODULE_PATH` route.
3. PDF viewer: accept native `<object>` as the default (target browsers have built-in viewers), or keep PDF.js as the guaranteed renderer (lazy)?
4. servicios "30 días": keep as a `PERIOD_DAYS` constant, or compute from `start_date`/`end_date` if those exist on the subscription?
5. avisos: remove inline previews entirely (modal-only) to cut N-simultaneous PDF.js loads, or keep them but lazy?

## Ready for Proposal
**Yes** — but the user should answer the 5 open questions first (esp. #1 publicaciones access and #3 PDF-viewer strategy), since they change the design surface. After answers, proceed to `sdd-propose` → `sdd-design` → `sdd-spec` → `sdd-tasks` (strict_tdd: tests mandatory in apply).
