# Spec — 007-tema-personalizado

Capability: `tema-personalizado` (custom brand/theme without forking Tabler)

These are **delta** requirements over the current code. MUST/SHOULD/MAY follow
RFC 2119.

### Requirement: BRAND-CSS-OVERRIDE

The system SHALL apply brand theming through a project stylesheet that overrides
Tabler CSS variables, without editing `static/dist/css/tabler*.css`.

- **SHALL** provide `static/dist/css/theme.css` linked in
  `templates/includes/base/head.html` after `tabler.min.css`.
- **SHALL** re-declare a curated subset of `--tblr-*` variables
  (`--tblr-primary`, `--tblr-primary-rgb`, `--tblr-link`, `--tblr-secondary`).
- **SHALL NOT** modify `tabler.min.css` or `tabler-themes.min.css`.

#### Scenario: Global palette applied
- **Given** the site is loaded
- **When** `theme.css` is linked after `tabler.min.css`
- **Then** the rendered primary color equals the brand ocean-blue value
  (not Tabler's default `#066fd1`)

#### Scenario: No Tabler fork
- **Given** a reviewer inspects `static/dist/css/`
- **When** they diff `tabler*.css` against the vendored version
- **Then** those files are unchanged

### Requirement: DARK-MODE-BRAND

The system SHALL adapt dark mode to the brand palette via
`[data-bs-theme="dark"]` variable overrides.

- **SHALL** declare brand-tuned `--tblr-*` values under
  `[data-bs-theme="dark"]` in `theme.css`.
- **SHOULD** keep using the existing `data-bs-theme="dark"` mechanism
  (`templates/includes/base/head.html:20-22`).

#### Scenario: Brand-aware dark mode
- **Given** the user enables dark mode
- **When** the page renders with `data-bs-theme="dark"`
- **Then** the palette uses the brand dark variables, not the default inversion

### Requirement: PER-INSTANCE-CONFIG

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

#### Scenario: Instance re-theme without code
- **Given** an operator updates `primary_color` on `SiteConfiguration`
- **When** the page is rendered
- **Then** the applied `--tblr-primary` reflects the new value without a deploy
  change to Tabler or component templates

### Requirement: FAVICON

The system SHALL serve a CMP Camagüey favicon.

- **SHALL** keep `static/dist/img/favicon.ico` as the CMP Camagüey mark.
- **MAY** override the `href` in `templates/includes/base/head.html:6-8` from
  `SiteConfiguration.favicon` when set.

#### Scenario: Favicon rendered
- **Given** the site HTML head
- **When** the browser requests the favicon URL
- **Then** the CMP Camagüey icon is returned

### Requirement: LOGO

The system SHALL render the CMP/INSMET brand mark in the navbar, sidebar, and
footer.

- **SHALL** keep `templates/includes/logo.html` as the default inline SVG.
- **SHALL** render `SiteConfiguration.brand_logo.url` when present, in
  `home/navbar.html:16`, `dashboard/sidebar.html:17`, `home/footer.html:70-86`.

#### Scenario: Default brand mark
- **Given** no `brand_logo` is configured
- **When** the navbar/sidebar/footer render
- **Then** the inline CMP/INSMET SVG is shown

#### Scenario: Overridden brand mark
- **Given** `SiteConfiguration.brand_logo` is set
- **When** the navbar/sidebar/footer render
- **Then** the configured image is shown instead of the inline SVG

### Requirement: NO-REGRESSION

- **SHALL NOT** regress existing Tabler components or the runtime theme
  switcher (`settings.html` / `scripts.html`).
- **SHALL** pass `python manage.py check`, `python manage.py test apps.core`,
  and `djlint --reformat --check` on touched templates.

### Requirement: SITECONFIG-EDIT-PAGE

The system SHALL expose editing of the `SiteConfiguration` singleton (primary
color, theme base, brand logo, favicon) in the dashboard web UI, mirroring the
`CompanySettingsUpdateView` pattern, so operators no longer need Django admin.

- **SHALL** provide `SiteConfigurationUpdateView` with
  `LoginRequiredMixin` + `PermissionRequiredMixin` and
  `permission_required = 'core.change_siteconfiguration'`, following
  `apps/core/views/company_settings.py` (singleton `get_object()`,
  `log_action`, `messages.success`, `reverse_lazy`).
- **SHALL** serve the form at `core:site_configuration`
  (`configuracion-sitio/` in `apps/core/urls.py`).
- **SHALL** render `brand_logo` and `favicon` as multipart file inputs
  (`enctype="multipart/form-data"`); file lifecycle follows
  `FileHandlerMixin` + `file_fields` (`apps/core/models.py:154`).
- **SHALL** validate `primary_color` as `#RRGGBB` hex.
- **SHALL** persist changes to the same singleton row consumed by the
  `site_branding` context processor (`apps/core/context_processors.py:11`).

#### Scenario: Operator saves branding from the web

- **Given** an authenticated user with `core.change_siteconfiguration`
- **When** they submit `configuracion-sitio/` changing `primary_color`,
  `theme_base`, `brand_logo`, and `favicon`
- **Then** the singleton row reflects the new values immediately
- **And** subsequent renders via `site_branding` expose them

#### Scenario: Permission denied

- **Given** an authenticated user without `core.change_siteconfiguration`
- **When** they request `configuracion-sitio/`
- **Then** the request SHALL be denied (403) and no mutation occurs

#### Scenario: Invalid hex rejected

- **Given** the edit page
- **When** a non-hex `primary_color` (e.g. `"red"`, `"#12345"`) is submitted
- **Then** the form SHALL display a validation error and SHALL NOT persist

### Requirement: PRIMARY-COLOR-AUTHORITATIVE

`SiteConfiguration.primary_color` SHALL be the authoritative persistent site
color. The default SHALL change from `#0b6e99` to `#2b4b9b` (gateway blue of
the CMP mark), and the existing singleton row SHALL be updated accordingly.

- **SHALL** set the model default of `primary_color` to `#2b4b9b`
  (`apps/core/models.py:145`).
- **SHALL** update the existing `SiteConfiguration` row to `#2b4b9b` via a
  migration data update (project convention: migrations are not versioned).
- **SHALL** apply the seeded model hex as the rendered primary color on first
  load — as a CSS variable — because `tabler-themes.min.css` presets only match
  named swatches and a hex `data-bs-theme-primary` value matches no preset.
- **SHALL** make the switcher's "Restablecer" (`#reset-changes`,
  `templates/includes/base/settings.html:281`) clear localStorage and re-apply
  the model value.
- **MAY** keep the named Tabler swatches (`green`, `teal`, …) as a
  visitor-local override, stored in `localStorage['tabler-theme-primary']`
  per Tabler semantics.
- **SHALL NOT** let a visitor swatch selection become the site's persistent
  color: the model value SHALL win on load and on reset.

#### Scenario: Fresh visitor renders the model color

- **Given** no `tabler-theme-primary` in localStorage
- **When** the page renders with `SiteConfiguration.primary_color = #2b4b9b`
- **Then** the applied `--tblr-primary` SHALL be `#2b4b9b`

#### Scenario: Operator re-themes the site

- **Given** `SiteConfiguration.primary_color` is changed via the edit page
- **When** a visitor without a stored override loads the site
- **Then** the rendered primary color reflects the new model value

#### Scenario: Reset returns to the model

- **Given** a visitor who selected the `green` swatch (stored in localStorage)
- **When** they click "Restablecer"
- **Then** `localStorage['tabler-theme-primary']` SHALL be removed
- **And** the applied primary color SHALL be the model's `#2b4b9b`, not green

### Requirement: THEME-CSS-RECONCILED

The system SHALL reconcile `static/dist/css/theme.css` so its hardcoded values
no longer conflict with the model.

- **SHALL NOT** hardcode `--tblr-primary: #0b6e99` (the obsolete default) or
  the old green `--tblr-secondary` values (`#1a8a5c` light, `#28a745` dark)
  as site-wide winners over the model.
- **SHALL** keep brand-tuned dark mode under `[data-bs-theme="dark"]`
  consistent with the new default `#2b4b9b`.
- **SHALL NOT** modify `tabler.min.css` or `tabler-themes.min.css`.

#### Scenario: No stale palette wins

- **Given** `theme.css` is inspected
- **When** comparing its hardcoded values against `primary_color = #2b4b9b`
- **Then** `theme.css` SHALL NOT override the model value with `#0b6e99`
  or a green secondary

### Requirement: LOGO-FIXED

The CMP/INSMET logo identity SHALL remain unchanged.

- **SHALL** keep the `#2b4b9b` / `#e5201e` fills and the stroke
  `#2b4b9b` in `templates/includes/logo.html` untouched.
- **SHALL** keep `static/dist/img/logo.svg` untouched.
- **SHALL** rely on `navbar-brand-autodark` for dark-mode logo contrast;
  no color-swap logic SHALL be added.
- **SHALL** continue rendering `SiteConfiguration.brand_logo.url` when set,
  per the existing LOGO requirement of 007.

#### Scenario: Logo unchanged

- **Given** the repository after this change
- **When** `git diff` is inspected for `templates/includes/logo.html` and
  `static/dist/img/logo.svg`
- **Then** those files SHALL show no changes

### Requirement: NO-REGRESSION-019

- **SHALL NOT** regress the runtime theme switcher, Tabler components, or the
  `site_branding` context processor.
- **SHALL** pass `python manage.py check`, `python manage.py test apps.core`,
  and `djlint --reformat --check` on touched templates.
### Requirement: LIGHT-DEFAULT-EXPLICIT

The portal SHALL render light mode by default regardless of OS
`prefers-color-scheme`. When the resolved theme is not dark, `head.html`
SHALL set `data-bs-theme="light"` on `<html>` server-side (the 1.5.1 default
is `auto`, which would follow the OS and render the portal dark on dark
systems).

#### Scenario: OS-dark visitor sees light

- GIVEN an OS in dark mode and no stored `tabler-theme` choice
- WHEN the portal loads (landing, home or dashboard)
- THEN `<html>` carries `data-bs-theme="light"`
- AND the page renders the light palette

#### Scenario: Dark choice still wins

- GIVEN a stored `tabler-theme=dark` or a `?theme=dark` URL
- WHEN the portal renders
- THEN `<html>` carries `data-bs-theme="dark"`
- AND the navbar `?theme=light` link switches back to explicit light

### Requirement: THEME-LOADER-151

The patched `tabler-theme.min.js`, re-derived on the 1.5.1 base and
documented in its provenance header, SHALL manage ONLY the light/dark toggle
and SHALL NOT read or write `data-bs-theme-base`, `data-bs-theme-font`,
`data-bs-theme-primary` or `data-bs-theme-radius`, nor their `tabler-*`
localStorage keys (1.5.1 mechanism: `tabler-<key>` localStorage to
`data-bs-*` attribute).

#### Scenario: Model theme attrs survive

- GIVEN `site_branding` seeds `data-bs-theme-base` (plus font/primary/radius)
  on `<html>`
- WHEN the patched loader runs and the visitor toggles light/dark
- THEN the four admin-seeded attributes remain unchanged

#### Scenario: Toggle persists across reloads

- GIVEN the visitor follows a navbar `?theme=dark` link
- WHEN the page reloads
- THEN the choice is read from `localStorage["tabler-theme"]` and applied
  before first paint, with no flash of the wrong mode

### Requirement: THEME-BASE-020-VERIFIED

The `data-bs-theme-base` contract (change 020) SHALL survive the 1.5.1
upgrade: the five model choices (slate, gray, zinc, neutral, stone) SHALL
resolve in the vendored `tabler-themes.min.css`, with `gray` as the default.

#### Scenario: All presets resolve

- GIVEN the page rendered with each of the five model `theme_base` values
- WHEN the page is inspected
- THEN the expected gray-scale palette applies (no unstyled fallback)
- AND `gray` renders identically to Tabler's built-in default

#### Scenario: No theme regression

- GIVEN the portal before and after the upgrade
- WHEN both render with the same `site_branding` values
- THEN the applied palette looks identical (no brand-breaking visual drift)
