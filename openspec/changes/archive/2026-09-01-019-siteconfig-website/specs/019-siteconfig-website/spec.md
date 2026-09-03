# Spec — 019-siteconfig-website

Capability: `tema-personalizado` (extended: web-managed `SiteConfiguration` +
model-authoritative site color). Delta requirements over `openspec/specs/007-tema-personalizado/spec.md`.

These are **delta** requirements over the current code. MUST/SHOULD/MAY follow
RFC 2119.

## Requirement: SITECONFIG-EDIT-PAGE

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

### Scenario: Operator saves branding from the web

- **Given** an authenticated user with `core.change_siteconfiguration`
- **When** they submit `configuracion-sitio/` changing `primary_color`,
  `theme_base`, `brand_logo`, and `favicon`
- **Then** the singleton row reflects the new values immediately
- **And** subsequent renders via `site_branding` expose them

### Scenario: Permission denied

- **Given** an authenticated user without `core.change_siteconfiguration`
- **When** they request `configuracion-sitio/`
- **Then** the request SHALL be denied (403) and no mutation occurs

### Scenario: Invalid hex rejected

- **Given** the edit page
- **When** a non-hex `primary_color` (e.g. `"red"`, `"#12345"`) is submitted
- **Then** the form SHALL display a validation error and SHALL NOT persist

## Requirement: PRIMARY-COLOR-AUTHORITATIVE

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

### Scenario: Fresh visitor renders the model color

- **Given** no `tabler-theme-primary` in localStorage
- **When** the page renders with `SiteConfiguration.primary_color = #2b4b9b`
- **Then** the applied `--tblr-primary` SHALL be `#2b4b9b`

### Scenario: Operator re-themes the site

- **Given** `SiteConfiguration.primary_color` is changed via the edit page
- **When** a visitor without a stored override loads the site
- **Then** the rendered primary color reflects the new model value

### Scenario: Reset returns to the model

- **Given** a visitor who selected the `green` swatch (stored in localStorage)
- **When** they click "Restablecer"
- **Then** `localStorage['tabler-theme-primary']` SHALL be removed
- **And** the applied primary color SHALL be the model's `#2b4b9b`, not green

## Requirement: THEME-CSS-RECONCILED

The system SHALL reconcile `static/dist/css/theme.css` so its hardcoded values
no longer conflict with the model.

- **SHALL NOT** hardcode `--tblr-primary: #0b6e99` (the obsolete default) or
  the old green `--tblr-secondary` values (`#1a8a5c` light, `#28a745` dark)
  as site-wide winners over the model.
- **SHALL** keep brand-tuned dark mode under `[data-bs-theme="dark"]`
  consistent with the new default `#2b4b9b`.
- **SHALL NOT** modify `tabler.min.css` or `tabler-themes.min.css`.

### Scenario: No stale palette wins

- **Given** `theme.css` is inspected
- **When** comparing its hardcoded values against `primary_color = #2b4b9b`
- **Then** `theme.css` SHALL NOT override the model value with `#0b6e99`
  or a green secondary

## Requirement: LOGO-FIXED

The CMP/INSMET logo identity SHALL remain unchanged.

- **SHALL** keep the `#2b4b9b` / `#e5201e` fills and the stroke
  `#2b4b9b` in `templates/includes/logo.html` untouched.
- **SHALL** keep `static/dist/img/logo.svg` untouched.
- **SHALL** rely on `navbar-brand-autodark` for dark-mode logo contrast;
  no color-swap logic SHALL be added.
- **SHALL** continue rendering `SiteConfiguration.brand_logo.url` when set,
  per the existing LOGO requirement of 007.

### Scenario: Logo unchanged

- **Given** the repository after this change
- **When** `git diff` is inspected for `templates/includes/logo.html` and
  `static/dist/img/logo.svg`
- **Then** those files SHALL show no changes

## Requirement: NO-REGRESSION

- **SHALL NOT** regress the runtime theme switcher, Tabler components, or the
  `site_branding` context processor.
- **SHALL** pass `python manage.py check`, `python manage.py test apps.core`,
  and `djlint --reformat --check` on touched templates.
