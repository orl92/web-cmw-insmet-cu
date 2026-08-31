# Spec — 007-tema-personalizado

Capability: `tema-personalizado` (custom brand/theme without forking Tabler)

These are **delta** requirements over the current code. MUST/SHOULD/MAY follow
RFC 2119.

## Requirement: BRAND-CSS-OVERRIDE

The system SHALL apply brand theming through a project stylesheet that overrides
Tabler CSS variables, without editing `static/dist/css/tabler*.css`.

- **SHALL** provide `static/dist/css/theme.css` linked in
  `templates/includes/base/head.html` after `tabler.min.css`.
- **SHALL** re-declare a curated subset of `--tblr-*` variables
  (`--tblr-primary`, `--tblr-primary-rgb`, `--tblr-link`, `--tblr-secondary`).
- **SHALL NOT** modify `tabler.min.css` or `tabler-themes.min.css`.

### Scenario: Global palette applied
- **Given** the site is loaded
- **When** `theme.css` is linked after `tabler.min.css`
- **Then** the rendered primary color equals the brand ocean-blue value
  (not Tabler's default `#066fd1`)

### Scenario: No Tabler fork
- **Given** a reviewer inspects `static/dist/css/`
- **When** they diff `tabler*.css` against the vendored version
- **Then** those files are unchanged

## Requirement: DARK-MODE-BRAND

The system SHALL adapt dark mode to the brand palette via
`[data-bs-theme="dark"]` variable overrides.

- **SHALL** declare brand-tuned `--tblr-*` values under
  `[data-bs-theme="dark"]` in `theme.css`.
- **SHOULD** keep using the existing `data-bs-theme="dark"` mechanism
  (`templates/includes/base/head.html:20-22`).

### Scenario: Brand-aware dark mode
- **Given** the user enables dark mode
- **When** the page renders with `data-bs-theme="dark"`
- **Then** the palette uses the brand dark variables, not the default inversion

## Requirement: PER-INSTANCE-CONFIG

Branding SHALL be configurable per instance via the `SiteConfiguration`
singleton, with no code change per deployment.

- **SHALL** add `primary_color`, `theme_base`, `brand_logo`, `favicon` to
  `SiteConfiguration` (`apps/core/models.py:131`).
- **SHALL** make `SiteConfiguration` use `FileHandlerMixin` and declare
  `file_fields` for the `ImageField`s.
- **SHALL** expose the config via a context processor registered in
  `config/settings.py:139`.
- **SHALL** seed the `themeConfig` defaults in
  `templates/includes/base/scripts.html:9-17` from the context processor.

### Scenario: Instance re-theme without code
- **Given** an operator updates `primary_color` on `SiteConfiguration`
- **When** the page is rendered
- **Then** the applied `--tblr-primary` reflects the new value without a deploy
  change to Tabler or component templates

## Requirement: FAVICON

The system SHALL serve a CMP Camagüey favicon.

- **SHALL** keep `static/dist/img/favicon.ico` as the CMP Camagüey mark.
- **MAY** override the `href` in `templates/includes/base/head.html:6-8` from
  `SiteConfiguration.favicon` when set.

### Scenario: Favicon rendered
- **Given** the site HTML head
- **When** the browser requests the favicon URL
- **Then** the CMP Camagüey icon is returned

## Requirement: LOGO

The system SHALL render the CMP/INSMET brand mark in the navbar, sidebar, and
footer.

- **SHALL** keep `templates/includes/logo.html` as the default inline SVG.
- **SHALL** render `SiteConfiguration.brand_logo.url` when present, in
  `home/navbar.html:16`, `dashboard/sidebar.html:17`, `home/footer.html:70-86`.

### Scenario: Default brand mark
- **Given** no `brand_logo` is configured
- **When** the navbar/sidebar/footer render
- **Then** the inline CMP/INSMET SVG is shown

### Scenario: Overridden brand mark
- **Given** `SiteConfiguration.brand_logo` is set
- **When** the navbar/sidebar/footer render
- **Then** the configured image is shown instead of the inline SVG

## Requirement: NO-REGRESSION

- **SHALL NOT** regress existing Tabler components or the runtime theme
  switcher (`settings.html` / `scripts.html`).
- **SHALL** pass `python manage.py check`, `python manage.py test apps.core`,
  and `djlint --reformat --check` on touched templates.
