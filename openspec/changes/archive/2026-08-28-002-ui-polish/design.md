# Design — 002-ui-polish

## Overview

This change is a UI-consistency pass over the Tabler / Bootstrap 5 templates. It
touches no Python, no models, no URLs, and no migrations. The four work streams are
independent and can land separately, but share one principle: **one source of truth
per concern** (toast markup, loading indicator, radius/spacing, icon sizing).

## 1. Toast system — single source of truth

### Current state (verified)

- `static/dist/js/utils.js` defines `showToast(message, type, duration)` which:
  - resolves Bootstrap via `(window.tabler && window.tabler.bootstrap) || window.bootstrap`
    (`utils.js` top of function);
  - HTML-escapes the message before insertion (prevents XSS on dynamic messages);
  - renders one consistent markup with `ti ti-circle-check` / `ti ti-alert-triangle` /
    `ti ti-info-circle` / `ti ti-circle-x` (`utils.js:17,21,25,29`).
- It is loaded by `templates/includes/base/utils.html:6`, which is included from
  `templates/layouts/base.html:31` and `templates/layouts/base-auth.html:28`. Thus the
  global `showToast` already exists on every authenticated page.

### Problems

1. **Duplicate `#toast-container` ids** — `templates/layouts/form.html:11-12` and
   `apps/user_auth/templates/pages/user_auth/users/register.html:7-8` each re-declare
   the container, although `utils.html` already provides it. Duplicate ids are invalid
   HTML and make `getElementById('toast-container')` ambiguous.
2. **Shadowed reimplementations** — `register.html:484` and `invoice/create.html:284`
   declare a local `function showToast(...)`. Because `invoice/create.html` extends
   `layouts/form.html` (`…/invoice/create.html:1`) the canonical helper is loaded, so
   the inline version silently overrides it, producing a *different* visual language
   (colored `bg-success`/`bg-danger` headers, `ti ti-check`).

### Plan

- Delete `templates/layouts/form.html:11-12` (the inline container).
- Delete `apps/user_auth/templates/pages/user_auth/users/register.html:7-8`
  (the inline container) and refactor its toast calls to use the global `showToast()`.
- Replace the inline `showToast` bodies at `register.html:484` and
  `invoice/create.html:284` with calls to `window.showToast(message, type, duration)`.
- Keep `static/dist/js/utils.js` as the only implementation. No behavioral change to
  escaping or icon set.

### Risk / verification

- `register.html` and `invoice/create.html` already have the global `showToast` from
  `utils.html`, so removing the local copies cannot break toast rendering. Verify by
  triggering a validation error toast on both pages and confirming the Tabler
  `ti ti-circle-x` markup appears.

## 2. DataTables loading indicator

### Current state (verified)

- `templates/layouts/list.html:46-55` initializes
  `new DataTable('#{{ list_id|default:'example' }}', { language: { url: Spanish.json } })`.
- `apps/meteo/templates/pages/meteo/forecast/list.html` has a second DataTable init
  with the same shape.
- Neither sets `processing`. Per `AGENTS.md`, DataTables load all rows client-side, so
  the initial paint and client-side sort/filter happen with no feedback.

### Plan

- Add `processing: true` to both `new DataTable(...)` option objects.
- Style the DataTables processing element in `static/dist/css/utils.css`:
  `.dataTables_processing` → centered overlay, Bootstrap `spinner-border` +
  `.text-muted` label, matching the Tabler surface, with `z-index` above the table.
- This automatically covers the 22 templates that extend `layouts/list.html`.

### Risk / verification

- `processing` is a stable DataTables option; no layout shift beyond the brief overlay.
- Verify on any list view (e.g. a commercial list) that a spinner shows during the
  initial render and during a column sort.

## 3. Spacing / radius utilities

### Current state (verified)

- `templates/layouts/list.html:26`:
  `<div class="card-body p-4 table-responsive" style="border-radius: 10px;">`
- `apps/meteo/templates/pages/meteo/forecast/list.html:44`: same inline
  `border-radius: 10px;`.
- Repo-wide: 26 inline `border-radius` occurrences in templates.

### Plan

- Replace the inline `border-radius: 10px;` on both cards with `rounded-3` so the
  radius follows the Tabler spacing scale already established by `p-4`.
- Audit the remaining 24 inline `border-radius` occurrences; for those that encode
  radius only, convert to `rounded-*`; for ones mixed with other properties, convert
  only the radius portion. Do **not** introduce arbitrary new radius values.

### Risk / verification

- `rounded-3` = 0.5rem, visually close to the previous 10px. Low visual delta.
- `djlint --lint` confirms no leftover inline `border-radius` in the two primary files.

## 4. Icon markup normalization

### Current state (verified)

- Standard: 170 `<i class="icon ti ti-…">` (`.icon` is Tabler's sizing hook).
- Bare: 23 `<i class="ti ti-…">` missing the `icon` class → inconsistent glyph size.
- One anomaly: `templates/includes/base/settings.html:282`
  `<i class="icon icon-1 ti ti-refresh">` — `icon-1` is not a Tabler class.

### Plan

- Add `icon` to the 23 bare `<i class="ti ti-…">` icons.
- Replace `icon-1` at `settings.html:282` with `icon` (add an explicit `style="…"`
  font-size only if a deliberate smaller size is wanted; otherwise drop `icon-1`).

### Risk / verification

- Pure class addition; no logic change. Confirm glyph sizes are uniform with a visual
  pass over a list/form page.

## Cross-cutting

- Run `djlint . --reformat --check` and `djlint . --lint` over every touched template
  (email templates under `*/emails/` are excluded from reformatting per `AGENTS.md`).
- Run `python manage.py check` (no model changes, but confirms templates still load).
- No new tests are required; this is presentational. If a regression harness is wanted,
  a simple view smoke test that renders a list and a form page and asserts a single
  `#toast-container` would guard the duplicate-container regression.
