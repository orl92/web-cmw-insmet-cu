# Proposal

## Intent

Polish the Tabler / Bootstrap 5 UI across the Django templates to improve visual
consistency, spacing rhythm, icon usage, responsive behavior, and user-feedback
states (toasts, loading indicators). This is pure front-end / template polish on
existing views — no data-model, URL, or Python view changes.

The work is scoped to the 169 templates under `templates/` and `apps/*/templates/`,
where 46 pages extend `layouts/form.html` and 22 extend `layouts/list.html`
(signal: `grep -rl "extends 'layouts/form.html'"` / `"extends 'layouts/list.html'"`).

## Scope In

- **Toast unification** — make `showToast()` in `static/dist/js/utils.js` the single
  source of truth and remove duplicate `#toast-container` nodes and inline
  `showToast` reimplementations.
- **DataTables loading state** — show a processing/loading indicator while DataTables
  initialize and during sort/filter.
- **Spacing / radius utilities** — replace inline `border-radius` styles with the
  Tabler radius utilities (`rounded-3` / `rounded-4`).
- **Icon markup normalization** — use the Tabler sizing hook (`<i class="icon ti ti-…">`)
  consistently across all templates.

## Scope Out

- No model, migration, URL, or Python view changes (no `makemigrations` needed).
- No new CSS frameworks or component libraries — Tabler only, per `AGENTS.md`
  ("UI Framework: exclusivamente Tabler.io (Bootstrap 5)").
- No auth, permission, or behavioral changes.
- **Django `messages` framework**: not used in any template today
  (`grep -rl "messages\." templates apps --include="*.html"` → 0 hits), so there is
  no `messages` ↔ `showToast` unification to perform.
- **Commercial table horizontal scroll <768px**: already satisfied because all 6
  commercial list templates extend `layouts/list.html`, whose `card-body` is wrapped
  in `table-responsive` (`templates/layouts/list.html:26`). This is a verify-only item,
  not an implementation item.

## Approach

All evidence below is anchored to the current working tree.

### 1. Unify the toast / notification system

- Canonical helper: `showToast(message, type, duration)` in
  `static/dist/js/utils.js` (lines ~1–60), using `Bootstrap.Toast`, HTML-escaping the
  message, and Tabler icons `ti ti-circle-check` / `ti ti-alert-triangle` /
  `ti ti-info-circle` / `ti ti-circle-x` (`static/dist/js/utils.js:17,21,25,29`).
  It is loaded on every page via `templates/includes/base/utils.html:6`, included from
  `templates/layouts/base.html:31` and `templates/layouts/base-auth.html:28`.
- Duplicate container — `templates/layouts/form.html:11-12` re-declares
  `<div id="toast-container">`, even though `base.html` already injects it via
  `utils.html`. Because `form.html` is extended by 46 templates, 46 pages carry a
  second element with the same `id`. **Remove lines 11-12.**
- Duplicate container — `apps/user_auth/templates/pages/user_auth/users/register.html:7-8`
  also re-declares `#toast-container`; its parent `base-auth.html` already includes
  `utils.html`. **Remove lines 7-8.**
- Divergent inline reimplementation — `register.html` defines its own `showToast`
  (`apps/user_auth/templates/pages/user_auth/users/register.html:484`) using colored
  `bg-success` / `bg-danger` header classes and `ti ti-check` / `ti ti-info-circle`.
- Divergent inline reimplementation — `invoice/create.html` defines its own
  `showToast` (`apps/commercial/templates/pages/commercial/invoice/create.html:284`).
  Crucially, `invoice/create.html` extends `layouts/form.html` (`…/invoice/create.html:1`),
  so the canonical `utils.js` `showToast` is already loaded and the inline version
  **shadows** it — two different toast visual languages on one page.
  **Delete both inline `showToast` blocks and call the global `showToast()` instead.**

### 2. DataTables loading indicator

- Two DataTable initializations exist:
  `templates/layouts/list.html:46-55` and
  `apps/meteo/templates/pages/meteo/forecast/list.html` (the forecast list init).
  Neither sets `processing`, so there is no feedback during the initial render or
  during client-side sort/filter.
- Add `processing: true` to both `new DataTable(...)` configs and style
  `.dataTables_processing` to match Tabler (Bootstrap spinner + muted text) in
  `static/dist/css/utils.css`. This covers the 22 templates that extend `list.html`.

### 3. Spacing / radius utilities

- Inline radius is used instead of a utility at
  `templates/layouts/list.html:26` (`style="border-radius: 10px;"`) and
  `apps/meteo/templates/pages/meteo/forecast/list.html:44` (same inline style).
  A repo-wide scan finds 26 inline `border-radius` occurrences in templates.
- Replace radius-only inline styles with `rounded-3` (0.5rem) to match the existing
  `p-4` padding rhythm, and audit the remaining 24 occurrences to convert the radius
  portion to utilities where it encodes radius only.

### 4. Icon markup normalization

- Tabler sizes glyphs via the `.icon` hook. Current usage: 170 `<i class="icon ti ti-…">`
  vs 23 `<i class="ti ti-…">` that omit `icon`, producing inconsistent glyph sizes.
- One non-standard class: `templates/includes/base/settings.html:282`
  (`<i class="icon icon-1 ti ti-refresh">`) — `icon-1` is not a Tabler class.
- Add the `icon` class to the 23 bare `<i class="ti ti-…">` icons and replace
  `icon-1` with the standard `icon` sizing (explicit size via inline `style` if needed).

## Acceptance Criteria

- [ ] Every page has exactly one `#toast-container` node (canonical one from
      `templates/includes/base/utils.html`).
- [ ] No template re-defines a `showToast` function; `register.html` and
      `invoice/create.html` call the global `showToast()` from `utils.js`.
- [ ] All toasts use the same Tabler markup (icon set `ti ti-circle-check` /
      `ti ti-alert-triangle` / `ti ti-info-circle` / `ti ti-circle-x` and the
      `Bootstrap.Toast` container from `utils.js`).
- [ ] Both DataTable initializations set `processing: true` and show a Tabler-styled
      processing indicator during load/sort/filter.
- [ ] No `style="border-radius: …"` remains in `list.html` or the meteo forecast
      list; radius is expressed with `rounded-*` utilities.
- [ ] All Tabler icons use the `icon` sizing class (no bare `ti ti-…`, no `icon-1`).
- [ ] Commercial list tables remain horizontally scrollable at <768px (no regression;
      already provided by `layouts/list.html` `table-responsive`).
- [ ] `djlint . --reformat --check` and `djlint . --lint` pass on touched templates.

## Rollback

All changes are confined to templates and `static/dist/js/utils.js` /
`static/dist/css/utils.css`. Revert via `git checkout -- <files>`; no migrations or
server restart beyond static re-collection (`collectstatic`) are required. No data
loss is possible because no model or migration is touched.
