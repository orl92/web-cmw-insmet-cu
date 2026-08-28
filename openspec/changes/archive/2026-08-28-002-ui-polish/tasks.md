# Tasks — 002-ui-polish

## Phase 1 — Toast unification (single source of truth)

- [x] Remove duplicate `#toast-container` from `templates/layouts/form.html` (lines 11-12)
- [x] Remove duplicate `#toast-container` from `apps/user_auth/templates/pages/user_auth/users/register.html` (lines 7-8)
- [x] Replace inline `showToast` reimplementation in `register.html` (line 484) with calls to the global `window.showToast()`
- [x] Replace inline `showToast` reimplementation in `apps/commercial/templates/pages/commercial/invoice/create.html` (line 284) with calls to the global `window.showToast()`
- [x] Verify every page has exactly one `#toast-container` and toasts use the `utils.js` markup (`ti ti-circle-check` / `ti ti-alert-triangle` / `ti ti-info-circle` / `ti ti-circle-x`)

## Phase 2 — DataTables loading indicator

- [x] Add `processing: true` to the DataTable init in `templates/layouts/list.html` (lines 46-55)
- [x] Add `processing: true` to the DataTable init in `apps/meteo/templates/pages/meteo/forecast/list.html`
- [x] Add Tabler-styled `.dataTables_processing` rules to `static/dist/css/utils.css` (spinner + muted label)
- [x] Verify the spinner shows on initial render and on column sort/filter of a list view

## Phase 3 — Spacing / radius utilities

- [x] Replace inline `border-radius: 10px;` with `rounded-3` in `templates/layouts/list.html` (line 26)
- [x] Replace inline `border-radius: 10px;` with `rounded-3` in `apps/meteo/templates/pages/meteo/forecast/list.html` (line 44)
- [x] Audit the remaining inline `border-radius` occurrences in templates and convert the radius portion to `rounded-*` utilities

## Phase 4 — Icon markup normalization

- [x] Add the `icon` class to the 23 bare `<i class="ti ti-…">` icons across templates
- [x] Remove the non-standard `icon-1` class at `templates/includes/base/settings.html` (line 282), keeping `icon` sizing

## Phase 5 — Verification

- [x] Run `djlint . --reformat --check` and `djlint . --lint` on touched templates
- [x] Run `python manage.py check`
- [x] Confirm commercial list tables remain horizontally scrollable at <768px (no regression; already provided by `layouts/list.html` `table-responsive`)
