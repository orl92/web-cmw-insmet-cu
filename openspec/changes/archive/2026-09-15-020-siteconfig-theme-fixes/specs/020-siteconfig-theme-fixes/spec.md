# Spec — 020-siteconfig-theme-fixes

Capability: `020-siteconfig-theme-fixes` (delta over 019 `siteconfig-website`)

These are **delta** requirements over current code (MUST/SHOULD/MAY per RFC
2119).

### Requirement: THEME-BASE-APPLIED

The system SHALL render the admin theme from `SiteConfiguration` as `data-bs-*`
attributes on `<html>` with model authority (admin-only); the visitor light/dark
toggle stays separate.

- **SHALL** apply model admin keys `theme-base`/`theme-font`/`theme-radius`/
  `theme-primary` on `document.documentElement` — before first paint
  (`head.html`) and on `DOMContentLoaded` (`scripts.html`).
- **SHALL** set `data-bs-theme-primary` to the model primary (swatch name or
  hex) plus inline `--tblr-primary`/`--tblr-primary-rgb`.
- **SHALL NOT** read `localStorage['tabler-*']` for base/font/radius/primary —
  no visitor override of the admin theme.
- **SHALL** keep the visitor light/dark toggle on `data-bs-theme`
  (`?theme=…`/`localStorage['tabler-theme']`/default `light`), managed by
  `tabler-theme.min.js`.

#### Scenario: Model theme renders on load

- **Given** `theme_base="neutral"`, `theme_font="sans-serif"`,
  `theme_radius="1"`, `primary_color="#2b4b9b"`
- **When** the page loads
- **Then** `document.documentElement` SHALL carry
  `data-bs-theme-base="neutral"`, `data-bs-theme-font="sans-serif"`,
  `data-bs-theme-radius="1"`, `data-bs-theme-primary="#2b4b9b"` and inline
  `--tblr-primary: #2b4b9b` before first paint

#### Scenario: Visitor light/dark never touches admin theme

- **Given** `localStorage['tabler-theme'] === "dark"` and
  `theme_base="neutral"` in the model
- **When** the page loads
- **Then** `data-bs-theme` SHALL be `"dark"` while `data-bs-theme-base` SHALL
  remain `"neutral"`

### Requirement: RESET-RESTORES-MODEL

"Restablecer tema" SHALL restore the `SiteConfiguration` model defaults through
a server-side action; no client-side reset exists.

- **SHALL** render a "Restablecer tema" button in page-header `title_actions`
  opening a confirmation modal; submitting POSTs `reset_theme_defaults` to
  `core:site_configuration`.
- **SHALL** restore the model defaults `#2b4b9b`/`neutral`/`sans-serif`/`1`,
  log the action and redirect; the next render applies them.
- **SHALL NOT** clear visitor `localStorage` or remove attributes client-side
  (the floating switch and its client reset were removed).

#### Scenario: Reset restores model defaults

- **Given** `SiteConfiguration` holds `primary_color='#123456'`,
  `theme_base='zinc'`, `theme_font='serif'`, `theme_radius='2'`
- **When** an operator with `core.change_siteconfiguration` submits the reset
  modal
- **Then** the model SHALL hold `#2b4b9b`/`neutral`/`sans-serif`/`1` after the
  redirect, and the next render SHALL apply those values

### Requirement: THEME-CSS-PRIMARY-ONLY

`static/dist/css/theme.css` SHALL customize only the brand primary in dark
mode; all other variables SHALL remain Tabler defaults.

- **SHALL NOT** override `--tblr-link`.
- **SHALL** keep under `[data-bs-theme="dark"]` only `--tblr-primary` /
  `--tblr-primary-rgb` at `#2b4b9b` / `43, 75, 155`.
- **SHALL** leave light-mode primary set at runtime from the model, not
  hardcoded.

#### Scenario: Only primary customized

- **Given** `theme.css` is inspected
- **When** comparing its declared variables to the full Tabler set
- **Then** no variable beyond dark `--tblr-primary`/`--tblr-primary-rgb` SHALL
  be overridden

### Requirement: SETTINGS-FORM-STANDARD

`site/settings.html` SHALL follow the project's form-layout standard.

- **SHALL** extend `layouts/form.html` and define `{% block form %}` with
  section cards: "Colores y tema" (Coloris `primary_color` with hex validation
  plus `theme_base`/`theme_font`/`theme_radius` selects) and "Identidad"
  (`brand_logo` + `favicon`); the superuser-gated "Modo de mantenimiento" card
  with AJAX toggle stays in the same form.
- **SHALL** render `brand_logo` with a hint stating accepted formats
  (JPG/PNG/GIF only; SVG rejects validation) and a delete action when set.
- **SHALL** render `favicon` with a 64px preview avatar, "Ver imagen" lightbox
  link and delete action when set; else a file input with `accept` hint.
- **SHALL** keep `enctype="multipart/form-data"` and the
  `delete_logo`/`delete_favicon`/`toggle_maintenance` POST branches.

#### Scenario: Standard form shell

- **Given** an operator with `core.change_siteconfiguration` opens
  `configuracion-sitio/`
- **When** the page renders
- **Then** it SHALL use `layouts/form.html` with section cards for theme,
  identity and (superuser) maintenance

#### Scenario: Brand logo hint

- **Given** the edit page
- **When** the `brand_logo` field renders
- **Then** a hint SHALL state accepted formats JPG/PNG/GIF and that SVG is not
  accepted

#### Scenario: Favicon preview

- **Given** `SiteConfiguration.favicon` is set
- **When** the `favicon` field renders
- **Then** a 64px preview of the current image, a "Ver imagen" lightbox link
  and a delete action SHALL appear alongside the file input

### Requirement: NO-REGRESSION-020

- **SHALL NOT** change `logo.html` or the logo identity.
- **SHALL NOT** add build steps or npm/bundler dependencies; vendored minified
  libraries per project convention are allowed.
- **SHALL** permit exactly one documented patch to vendored
  `static/dist/js/tabler-theme.min.js` (Tabler 1.5.1, commit `c14686d`): the
  loader manages ONLY the visitor light/dark `data-bs-theme` and SHALL NOT
  touch `data-bs-theme-base/-font/-primary/-radius` — documented FOUC
  exception so it cannot wipe the admin theme pre-`scripts.html`. Further
  vendored edits require an explicit proposal exception.
- **SHALL** pass `python manage.py check`, `python manage.py test apps.core`,
  and `djlint --reformat --check` on touched templates.
