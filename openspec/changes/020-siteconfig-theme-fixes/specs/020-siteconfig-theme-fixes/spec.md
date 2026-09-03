# Spec — 020-siteconfig-theme-fixes

Capability: `020-siteconfig-theme-fixes` (delta over 019 `siteconfig-website`)

These are **delta** requirements over the current code. MUST/SHOULD/MAY follow
RFC 2119.

## Requirement: THEME-BASE-APPLIED

The system SHALL render the model-seeded base theme as a `data-bs-*` attribute
on `<html>`, not only as a checked radio.

- **SHALL** set every `themeConfig` key (including `theme-base`) as a
  `data-bs-*` attribute on `document.documentElement` during `DOMContentLoaded`
  in `templates/includes/base/scripts.html`, applying the
  `localStorage['tabler-<key>']` value when present, else the model value.
- **SHALL** keep marking the matching radios in the offcanvas as checked.
- **SHALL** apply the changes via the same mechanism the floating switch uses
  (attribute set on `<html>`), so a seeded base renders identically to a
  user-selected one.

### Scenario: Model base renders on load

- **Given** no `tabler-theme-base` override in localStorage
- **When** `SiteConfiguration.theme_base` is `"neutral"`
- **Then** `document.documentElement` SHALL carry `data-bs-theme-base="neutral"`
- **And** the neutral radio in the offcanvas SHALL be checked

### Scenario: Stored override wins on load

- **Given** `localStorage['tabler-theme-base'] === "slate"`
- **When** the page loads with model `theme_base = "neutral"`
- **Then** `data-bs-theme-base` SHALL be `"slate"`
- **And** the slate radio SHALL be checked

## Requirement: RESET-RESTORES-MODEL

Clicking "Restablecer" (`#reset-changes`) SHALL clear overrides and re-apply the
model values visually, not only mark radios.

- **SHALL** remove each `data-bs-*` attribute and the `localStorage['tabler-*']`
  entries on reset.
- **SHALL** then apply the model `themeConfig` values as `data-bs-*` attributes
  on `<html>` and call `applyTheme(model primary)`.
- **SHALL** check the radios to the model values afterwards.

### Scenario: Reset clears and applies model

- **Given** a visitor who selected the slate base and green primary
- **When** they click "Restablecer"
- **Then** `localStorage['tabler-theme-base']` and `['tabler-theme-primary']`
  SHALL be removed
- **And** `data-bs-theme-base` SHALL be the model value
- **And** the applied `--tblr-primary` SHALL be the model value, not green

## Requirement: THEME-CSS-PRIMARY-ONLY

`static/dist/css/theme.css` SHALL customize only the brand primary; all other
variables SHALL remain Tabler defaults.

- **SHALL NOT** override `--tblr-link` in `theme.css`.
- **SHALL** keep, under `[data-bs-theme="dark"]`, only `--tblr-primary` and
  `--tblr-primary-rgb` at the brand blue `#2b4b9b`.
- **SHALL** leave light-mode primary set at runtime by
  `templates/includes/base/scripts.html` (model authority), not hardcoded.

### Scenario: Only primary customized

- **Given** `theme.css` is inspected
- **When** comparing its declared variables to the full Tabler set
- **Then** SHALL NO variable beyond dark `--tblr-primary`/`--tblr-primary-rgb`
  be overridden

## Requirement: SETTINGS-FORM-STANDARD

`site/settings.html` SHALL follow the project's form layout standard.

- **SHALL** extend `layouts/form.html` and define sections in `{% block form %}`
  using `{% include 'includes/dashboard/form_card.html' with card_title=... %}`.
- **SHALL** render `brand_logo` with a small-hint clarifying accepted formats
  (JPG/PNG/GIF only; SVG rejects image validation).
- **SHALL** render `favicon` using the same image-design card as
  `service/update.html`: 64px preview avatar of the current image plus a
  "Ver imagen actual" lightbox link when set, and a file input with an
  `accept` hint when not.
- **SHALL** keep `enctype="multipart/form-data"` and the hex / file validation
  of the existing `SiteConfigurationForm`.

### Scenario: Standard form shell

- **Given** an operator with `core.change_siteconfiguration` opens
  `configuracion-sitio/`
- **When** the page renders
- **Then** it SHALL use `layouts/form.html` with `form_card` sections

### Scenario: Brand logo hint

- **Given** the edit page
- **When** the `brand_logo` field renders
- **Then** a hint SHALL state accepted formats JPG/PNG/GIF and that SVG is not
  accepted

### Scenario: Favicon preview

- **Given** `SiteConfiguration.favicon` is set
- **When** the `favicon` field renders
- **Then** a preview of the current image and a "Ver imagen actual" link SHALL
  appear alongside the file input

## Requirement: NO-REGRESSION-020

- **SHALL NOT** change `logo.html`, the logo identity, or Tabler vendored files.
- **SHALL NOT** add build steps or dependencies.
- **SHALL** pass `python manage.py check`, `python manage.py test apps.core`,
  and `djlint --reformat --check` on touched templates.
