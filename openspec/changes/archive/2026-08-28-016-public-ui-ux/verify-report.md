# Verification Report — 016-public-ui-ux

- **Change:** 016-public-ui-ux
- **Session mode:** Interactive (orchestrator reviews after phase)
- **Persistence:** BOTH — `openspec/changes/016-public-ui-ux/verify-report.md` + Engram (`sdd/016-public-ui-ux/verify-report`)
- **Django:** 5.1.4 (pinned) · Tabler only · Spanish · strict_tdd · djlint 2-space · apps under `apps/`
- **Date:** 2026-08-25

## Execution Evidence

| Check | Command | Result |
|---|---|---|
| Tests | `python manage.py test apps.meteo apps.home apps.publications apps.commercial` | **297 passed** (60.4s), OK |
| System check | `python manage.py check` | No issues (0 silenced) |
| djlint reformat | `djlint <7 touched templates> --reformat --check` | 0 files would be updated |
| djlint lint | `djlint <7 touched templates> --lint` | Linted 7 files, 0 errors |
| Targeted re-run | `python manage.py test apps.publications` | 21 passed (post-fix) |

`PermissionDenied` tracebacks in the suite are expected — they originate from tests asserting 403/permission behavior, not failures.

## Acceptance Criteria

| # | Criterion | Expected | Actual | Status |
|---|-----------|----------|--------|--------|
| 1 | `valid_until` saves `05/08/2026 02:30 PM` as aware Havana (no −4h shift) | Form accepts 12h Tempus string → aware `America/Havana`, wall-clock 14:30 preserved; `Warning.save()` make_aware naive; mgmt cmd idempotent | `forms/warning.py` has `input_formats=['%d/%m/%Y %I:%M %p', ...]`; `models.py:319-322` make_aware on naive; `normalize_warning_valid_until` dry-run no-op (tests pass) | **PASS** |
| 2 | "Ver PDF" → native `<object type="application/pdf">` modal, **lazy** (data set on `show.bs.modal`, no double-fetch), `<a download>` fallback | `<object type="application/pdf">`, initially empty `data`, JS sets it only on show; `<a download>` inside | `document_pdf_modal.html` has `<object … type="application/pdf">` + `<a … download>`; `document-modal.js` sets data only if changed (no double-fetch). `public_detail.html` previously passed `pdf_url` → **eager** `data`; **FIXED** (now lazy, like tiempo/avisos) | **PASS** (after minor fix) |
| 3 | Anonymous public detail from `layouts/home.html`; both "Ver PDF" and "Descargar" = `publicacion.pdf.url` | 200 + home layout; card `data-pdf-url` and `Descargar` href both `pdf.url` | `public_detail.html` extends `layouts/home.html`; card `data-pdf-url="{{ publicacion.pdf.url }}"` + `<a href="{{ publicacion.pdf.url }}" download>` (tests pass) | **PASS** |
| 4 | tiempo empty-state `alt` = "No hay pronósticos" | Both weather pages | `today.html:21` & `tomorrow.html:21` → `alt="No hay pronósticos"` | **PASS** |
| 5 | Modal triggers MUST be `<button>`, never `href="#"` | Changed templates use `<button>` | `document_card.html` uses `<button data-bs-toggle="modal" data-bs-target="#documentPdfModal">`; no `href="#"` modal triggers in changed templates | **PASS** (see note) |
| 6 | servicios: `Service.PERIOD_DAYS == 30`; `summary` sanitized; image `object-fit: contain` | constant 30; `summary\|sanitize_html`; `contain` | `models.py:94 PERIOD_DAYS = 30`; `service_detail.html:45 {{ service.summary\|sanitize_html }}`; `:14 object-fit: contain` (tests pass) | **PASS** |

## Issues / Adjustments

- **(Minor fix applied — transparently reported)** `apps/publications/templates/pages/publications/public_detail.html:33` passed `pdf_url=publicacion.pdf.url` to the modal include, which eagerly populated `<object data>` in HTML (PDF fetched on page load, violating the explicit "lazy" sub-requirement in criterion 2). Fixed to `{% include 'includes/home/document_pdf_modal.html' %}` so the `data` is empty initially and lazy-set by `document-modal.js` on `show.bs.modal` — consistent with tiempo/avisos. The card button already carries `data-pdf-url`, and the JS reads it, so both PDF actions still resolve to `pdf.url`. Publications suite re-ran green (21 passed).
- **(SUGGESTION / scope note)** `templates/includes/home/pdf_modal.html` (and the retained `pdf_preview.html` / `pdf-viewer.js`) still contain `href="#"` triggers. These are **intentionally retained** by design decision #2 (used by out-of-scope areas: commentaries, services public/commercial, publications list; asserted by `test_pdf_viewer_a11y.py`). They are outside this change's scope. If full a11y uniformity is later desired, a separate cleanup pass should convert those triggers to `<button>`. This does not block archive of 016.

## Overall Verdict

**READY FOR ARCHIVE** — all six acceptance criteria are satisfied; 297 tests pass; `check` and `djlint` clean. One minor deviation (eager PDF load in the public-publication modal) was corrected in place and reported; the remaining legacy `href="#"` artifacts are an explicit, documented design retention and are out of scope.
