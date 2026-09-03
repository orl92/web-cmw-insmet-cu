# Tasks: 020 — Site Config & Theme Fixes

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~120–180 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

## Phase 1: JS Theme Wiring (`scripts.html`)

- [x] 1.1 `templates/includes/base/scripts.html` — extract `applyConfig()` function: iterates `themeConfig`, sets `data-bs-<key>` on `document.documentElement` (value = `localStorage['tabler-<key>']` ?? model), then calls `checkItems()` to mark radios
- [x] 1.2 `DOMContentLoaded` — after existing `applyTheme(themeConfig["theme-primary"])`, add `applyConfig()` call to seed model base on load
- [x] 1.3 `#reset-changes` handler — after clearing `localStorage` and `data-bs-*` attrs and inline `--tblr-primary` vars, replace final `checkItems()` call with `applyTheme(themeConfig["theme-primary"])` then `applyConfig()` (re-seeds model + marks radios)

## Phase 2: CSS Cleanup (`theme.css`)

- [x] 2.1 `static/dist/css/theme.css` — remove `--tblr-link` line from `[data-bs-theme="dark"]` block; keep only `--tblr-primary: #2b4b9b` and `--tblr-primary-rgb: 43, 75, 155`

## Phase 3: Template Rework (`settings.html`)

- [x] 3.1 `apps/core/templates/pages/core/site/settings.html` — replace `{% extends 'layouts/dashboard.html' %}` with `{% extends 'layouts/form.html' %}`; rewrite body as `{% block form %}` with two `form_card` sections: "Colores y tema" (`primary_color` + `theme_base` side by side) and "Identidad" (`brand_logo` with format hint + `favicon` preview card)
- [x] 3.2 `brand_logo` field — add hint text: "Formatos: JPG, PNG, GIF. No se admiten SVG. Dejar en blanco si no desea cambiar el logo actual."
- [x] 3.3 `favicon` field — build image card mirroring `service/update.html` pattern: 64px `avatar-xl rounded` preview of current image, `with_invalid` file input, format hint, "Ver imagen actual" `data-fslightbox` link (group `site-favicon` — no collision since no other fslightbox groups exist in core templates)

## Phase 4: Verification

- [x] 4.1 `python manage.py check` — no errors
- [x] 4.2 `python manage.py test apps.core` — full suite passes (existing `test_site_configuration_branding.py` asserts `file_fields` unchanged; template/JS edits don't break model tests)
- [x] 4.3 `djlint apps/core/templates/pages/core/site/settings.html --reformat --check` — passes

## Phase 5: Image-field unification (user refinement)

- [x] 5.1 `apps/core/forms/site_configuration.py` — `brand_logo`/`favicon` widgets `ClearableFileInput` → `FileInput` (drop Django's "Actualmente:/Borrar" box)
- [x] 5.2 `apps/core/views/site_configuration.py` — add `post()` handling `delete_logo` + `delete_favicon` (mirror profile avatar delete pattern)
- [x] 5.3 `apps/core/templates/pages/core/site/settings.html` — logo + favicon side by side (`col-md-6`), avatar-style preview + "Ver imagen actual" + red Eliminar, manual file input (no raw `with_invalid` widget)
- [x] 5.4 `apps/core/templates/pages/core/company/settings.html` — migrate to `layouts/form.html` (form card sections)
- [x] 5.5 `apps/user_auth/templates/pages/user_auth/profile/update.html` — avatar preview fills available card space
- [x] 5.6 Tests — `test_site_configuration_template.py`: +6 (side-by-side, no-cartel, delete buttons, delete actions)

## Phase 6: Theme font/radius, Coloris picker, FOUC & avatar revert (second user refinement)

- [x] 6.1 `apps/core/models.py` — add `THEME_FONT_CHOICES` + `THEME_RADIUS_CHOICES`; add `theme_font` (default `sans-serif`) + `theme_radius` (default `1`) fields to `SiteConfiguration`
- [x] 6.2 Migration — non-versioned `0003_alter_siteconfiguration_theme_font_theme_radius` adds the two fields
- [x] 6.3 `apps/core/forms/site_configuration.py` — add fields to `fields` + `theme_font`/`theme_radius` `Select` widgets; `primary_color` → `TextInput` with `data-coloris` (clearable text field, not native swatch)
- [x] 6.4 Vendor `@melloware/coloris` 0.25.0 — `static/dist/libs/coloris/{coloris.min.css,coloris.min.js}` (no npm; fetch from jsDelivr)
- [x] 6.5 `settings.html` — `primary_color` renders as Coloris text input (swatches + clear able), add `theme_font` + `theme_radius` selects; load coloris CSS/JS + init in `{% block modal %}`
- [x] 6.6 FOUC — add inline synchronous theme-apply script in `templates/includes/base/head.html` (reads model `site_branding` + visitor localStorage; applies `data-bs-theme-base/font/radius` + `--tblr-primary`/`-rgb` before first paint); update `themeConfig` in `scripts.html` to read font/radius from model
- [x] 6.7 Avatar revert — `profile/update.html`: image back to fixed 64px rounded preview; the file-selector (and its hint) fills the available space with `flex-grow-1`
- [x] 6.8 Tests — `_valid_data()` updated (forms + views) for new required fields; +2 (theme_font/radius rendered; Coloris picker asset+attr) in `test_site_configuration_template.py`
- [x] 6.9 Verify — `manage.py check`, `manage.py test apps.core apps.user_auth`, `djlint`, `ruff`, detect-secrets; `makemigrations --check --dry-run` clean
- [x] 6.10 Commit — conventional commit including data migration + theme refinements

## Phase 7: Remove floating theme switch, admin-only theme, reset & Coloris polish

- [x] 7.1 Remove `templates/includes/base/settings.html` (floating theme switch) and its includes from `layouts/base.html` + `layouts/base-auth.html`; drop the commented offcanvas stub in `home/navbar.html`
- [x] 7.2 Keep the simple light/dark toggle already in both navbars (`?theme=…` + `hide-theme-dark/light` via `tabler-theme.min.js`)
- [x] 7.3 `scripts.html` — rework: apply font/radius/base/primary **only** from the model (no visitor localStorage override, no offcanvas change/reset listeners, no URL params); light/dark stays handled by `tabler-theme.min.js`
- [x] 7.4 `head.html` FOUC inline script — read only from the model (drop localStorage lookup for the admin-only settings), still applies `data-bs-*` + `--tblr-primary`/`-rgb` before first paint
- [x] 7.5 `apps/core/views/site_configuration.py` — `post()` handles `reset_theme_defaults` (restores primary `#2b4b9b`, base `neutral`, font `sans-serif`, radius `1`, logs action, redirects)
- [x] 7.6 `settings.html` — add "Restablecer valores por defecto" button (opens confirmation modal) + modal with submit `name="reset_theme_defaults"`
- [x] 7.7 Coloris picker — match Tabler demo: color stays inside the input, `selectInput:false`, `alpha:false`, `format:'hex'`, `focusInput:true`, and the 12 Tabler `--tblr-*` swatches (via `getComputedStyle` with hex fallbacks)
- [x] 7.8 Tests — `test_site_configuration_views.py` +`test_reset_theme_defaults_restores_defaults`; `test_site_configuration_template.py` +`test_reset_theme_defaults_button_and_modal`

## Phase 7b: FOUC fix — neutral is the default base, no theme flash

- [x] 7b.1 Root cause: `tabler-theme.min.js` iterated over `theme-base/-font/-primary/-radius` and, without a visitor `localStorage` value, fell back to its own defaults (`gray`, `blue`, …) which it then applied via `setAttribute`/`removeAttribute` — wiping the model's `neutral` applied by `head.html` and flashing Tabler's default (blue-ish) palette until `scripts.html` re-applied the model on DOMContentLoaded
- [x] 7b.2 Patch `tabler-theme.min.js` to manage ONLY the visitor light/dark `theme` (`?theme=` / `localStorage["tabler-theme"]` / default `light`) and never touch `data-bs-theme-base/-font/-primary/-radius` (admin-only, model-driven); node --check passes
- [x] 7b.3 `head.html` FOUC script — also apply the visitor light/dark (`?theme=...` / `localStorage["tabler-theme"]`) before first paint, so a saved dark mode never flashes the light palette first
- [x] 7b.4 `SiteConfiguration.theme_base` default changed `gray` → `neutral` (model + reset action + default assertion in `test_site_configuration_branding.py`); non-versioned migration `0004_alter_siteconfiguration_theme_base.py`
- [x] 7b.5 Verify — `manage.py check`, `manage.py test apps.core apps.user_auth` (176), `makemigrations --check --dry-run`, `djlint`, `ruff`, `node --check` on the patched loader
- [x] 7b.6 Commit — conventional commit fixing the theme FOUC (neutral default base, loader only handles light/dark)

## Phase 7c: Coloris runtime error + reset button in the page header

- [x] 7c.1 Root cause: Coloris `Uncaught TypeError: can't access property "setAttribute", d is undefined` — in @melloware/coloris 0.25.0 the `S()` (set/config) touches `d` (the `#clr-picker` element, created only by `z()`/init) in its `alpha`/`inline`/`theme` cases. Loading coloris as a blocking script deferred the auto-init `init()` to DOMContentLoaded, so `d` was still undefined when our `Coloris({alpha:false,…})` config ran in the DOMContentLoaded listener (`K()` is document-scoped, so `swatches` alone never triggered it). Tabler's demo loads coloris with `defer`, so `z()` runs synchronously (readyState "interactive") before the config `S` — this is why the Tabler pattern has no error
- [x] 7c.2 Card/envelope issue found: the coloris `<link>`/`<script>` + inline config lived in `{% block modal %}`, which `base.html` (line 27) AND `dashboard.html` (line 67) BOTH declare — so settings.html's `modal` block rendered TWICE, executing `coloris.min.js` twice. The 2nd execution's `z()` guard (`getElementById("clr-picker")`) saw `#clr-picker` already in the DOM from the 1st, so its own `d` stayed `undefined`; then its config `S` → `d.setAttribute` → TypeError (error fired at rendered lines 815 and 912, the two copies). `defer` alone does NOT fix this (verified on page)
- [x] 7c.3 Fix — move coloris out of `{% block modal %}` into blocks that render exactly once: `{% block extrastyle %}` (coloris.min.css in head) and `{% block extrajs %}` (coloris.min.js + inline config at body end). Single module scope now: auto-`init()` → `z()` runs before the config `S` on DOMContentLoaded. Verified rendered page has coloris.min.js/.css and `window.Coloris({`) exactly once each
- [x] 7c.4 Move the "Restablecer valores por defecto" button from inside the theme card to `{% block title_actions %}` (page-header action area). The button opens the modal via `data-bs-toggle`/`data-bs-target` (no form dependency); the modal stays inside the `{% block form %}` `<form>` so its `type="submit" name="reset_theme_defaults"` still POSTs and the view catches it
- [x] 7c.5 Verify — `djlint --check`, `manage.py check`, `manage.py test apps.core apps.user_auth` (176 OK), `ruff`; rendered page re-inspected for single coloris occurrence

## Phase 7d: Coloris field layout — full width + swatch in front of the hex code

- [x] 7d.1 Coloris wraps the picker input in a `.clr-field` span (`wrap:true`, default) with the swatch button positioned `right:0` (Coloris CSS) and `.clr-field` as `display:inline-block` — so the field did not fill its column and the color sat to the right of the hex code
- [x] 7d.2 Fix — replicate Tabler's `_coloris.scss` field pattern in a scoped `<style>` inside `{% block extrastyle %}` (coloris page only): `.clr-field{display:block;width:100%}` (fill the column), `.clr-field button{inset-inline-start:6px;inset-inline-end:auto;width:1.5rem;height:1.5rem;border-radius:var(--tblr-border-radius-pill)}` (round 24px disc inside the field, in front of the hex code), `.clr-field button::after{box-shadow:inset 0 0 0 1px var(--tblr-border-color-translucent)}` (subtle border), `.clr-field input{padding-inline-start:2.5rem}`. Using `--tblr-border-radius-pill` (100rem) guarantees a PERFECT circle regardless of the admin theme_radius (Tabler's own `var(--border-radius)` = 6px only gives rounded corners — user explicitly asked for round, not square-with-rounded-borders)
- [x] 7d.3 Verify — `djlint --check`, `manage.py check`, `manage.py test apps.core apps.user_auth` (176 OK); rendered page has the pill radius CSS and one `window.Coloris({`

## Phase 7e: Consolidate maintenance mode into the site settings template

- [x] 7e.1 The maintenance card is a third `col-12` card inside `{% block form %}`, placed AFTER the "Identidad" (logo/favicon) card so it sits between the identity fields and the "Aceptar"/"Cancelar" buttons. It is gated by `{% if request.user.is_superuser %}` so non-superusers never see or edit it. It uses the ORIGINAL Tabler switch (`form-switch form-switch-lg` checkbox with bare `id="maintenance_mode"`/`name`) with a status label "Activado"/"Desactivado" (`text-primary`/`text-muted`), layout: switch right-aligned (`col-md-4 ms-auto`), explanatory copy BELOW the switch as a muted helper paragraph (`mt-3`). The card header uses the SAME `subheader text-muted fw-medium mb-3` style as the sibling theme/identity cards (NO `card-header`, no icon)
- [x] 7e.2 Instant auto-toggle: the maintenance switch is NOT part of the Aceptar save. A small vanilla JS in `extrajs` listens for `change` on `#maintenance_mode` and POSTs only `toggle_maintenance=1&maintenance_mode=1|0` + csrf to `{% url 'core:site_configuration' %}` (X-Requested-With, Content-Type form-urlencoded), so it never drags files or half-edited theme fields. It updates `#maintenance-status` optimistically, shows a `showToast` success/danger toast, and rolls back on failure. This reproduces the old `MaintenanceModeToggleView` instant behavior (onchange auto-toggle) but without a full page reload, while the switch stays visually inside the single settings form. The main form itself no longer carries a `maintenance_mode` field
- [x] 7e.3 `SiteConfigurationUpdateView.post()` gained a `toggle_maintenance in request.POST` branch that runs BEFORE `super().post()`: it is superuser-gated (non-superuser returns `JsonResponse({ok:false}, 403)` and the flag is unchanged), flips `site.maintenance_mode` from `maintenance_mode=1|0`, records `log_action` "El usuario X activó/desactivó el modo de mantenimiento", and returns `JsonResponse({ok:true, maintenance_mode})`. `form_valid()` reverted to a plain save + generic success message (no maintenance coupling). `maintenance_mode` was removed from `SiteConfigurationForm.fields`/widgets
- [x] 7e.4 Remove the now-redundant separate maintenance surface: `MaintenanceModeToggleView` (views/maintenance.py), the `toggle-maintenance/` URL, the `toggle.html` template, the `MaintenanceModeToggleView` import+`__all__` export, and the "Mantenimiento" dropdown item + `'maintenance' in segment` conditions in `menu/_configuracion.html`. (Earlier rejected approaches: a `content_after` post-form card below the buttons; a `maintenance_mode` CheckboxInput field saved with Aceptar. The accepted design is the instant auto-toggle AJAX branch above)
- [x] 7e.5 Tests - `test_site_configuration_views.py`: non-superuser POSTing `toggle_maintenance=1&maintenance_mode=1` gets a 403 `{ok:false}` and the flag stays unchanged; superuser enabling (`maintenance_mode=1`) returns 200 `{ok:true, maintenance_mode:true}` and flips the flag; superuser disabling (`maintenance_mode=0`) returns 200 `{ok:true, maintenance_mode:false}` and flips the flag back. `test_site_configuration_template.py`: maintenance card present for superuser (shows "Modo de mantenimiento", "Desactivado", `id="maintenance_mode"`, `toggle_maintenance`), absent for non-superuser with the perm. Asserts the switch is the ORIGINAL Tabler form-switch style
- [x] 7e.6 Verify - full screen: `CheckUserProfileMiddleware` redirects users missing email/first_name/last_name to `profile_update`, so test users MUST carry those personal fields. `python -m djlint --check`, `python manage.py check` (0 issues), `python manage.py test apps.core apps.user_auth` (181 OK), `ruff check` clean; render probe: 200, ordered Identidad(favicon) < Modo de mantenimiento < Aceptar, switch uses `subheader` style (no `card-header`), csrf injected non-empty, AJAX enable and disable both return 200 with the correct flag. (Also aligned the stale `test_reset_theme_defaults_button_and_modal` to assert the current page-header label "Restablecer tema")

## Phase 7f: Maintenance mode must block EVERYONE (regression) + polish (user test feedback)

- [x] 7f.1 **Bug: maintenance mode stopped blocking anonymous users.** `MaintenanceModeMiddleware` required `request.user.is_authenticated`, so an anonymous visitor — or a just-logged-out superuser — sailed straight through to the public content instead of seeing the maintenance page. Rewrote the middleware: when `site_config.maintenance_mode` is on and `not request.user.is_superuser`, render `layouts/maintenance.html` with `status=503`; exempt only the login/logout paths. This restores the original pre-consolidation behavior (commit b1204d4) and matches the user's test (activate switch, log out → maintenance page with the "Iniciar sesión" button for the admin). WhiteNoise serves /static before this middleware, so the maintenance page assets still load. Tests: `test_maintenance_blocks_anonymous_user` added (anonymous GET → 503 + maintenance text); `test_maintenance_blocks_non_superuser` now expects 503 (not 302 redirect). Note: `assertContains` requires `status_code=503` when the body is a 503.

- [x] 7f.2 **Remove the icon from the maintenance card header** — the sibling theme/identity cards have no icons (`<h3 class="subheader text-muted fw-medium mb-3">` plain text). Removed the `<i class="ti ti-tool">`; updated the card copy to say the rest of the page is blocked and only superusers + the login route stay accessible.

- [x] 7f.3 **Toast feedback on toggle.** The maintenance switch now shows `showToast('El modo de mantenimiento ha sido activado/desactivado.', 'success')` after a successful AJAX toggle and a `danger` toast on failure (uses the global `showToast` from `utils.js`).

- [x] 7f.4 **Activity-log icon/family for maintenance.** The toggle handler now passes `action_flag=6` (the maintenance-specific family) instead of `CHANGE`(2), so the profile/activity timeline shows "Modo de Mantenimiento (activado/desactivado)" with the `ti-settings` icon (via `utils_filters.get_icon_for_action`/`action_description`) instead of the generic "Cambio" + `ti-edit`.

- [x] 7f.5 **Coloris dark mode.** Coloris opens a light picker on Tabler dark mode. Added `theme: dark|default` to the Coloris config, chosen by whether `documentElement` has `data-bs-theme="dark"` (Coloris `clr-dark` class applies its #444/#555 palette and light text).

- [x] 7f.6 Verify - `python -m djlint --check`, `python manage.py check` (0 issues), `python manage.py test apps.core apps.user_auth` (182 OK), `ruff check` clean; probe: toggle ON returns 200 JSON, last `ActivityLog.action_flag == 6`, logged-out superuser hitting `/` gets 503 maintenance page, login still 200.
