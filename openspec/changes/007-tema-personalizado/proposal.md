# Proposal

## Intent

Establish a custom brand/theme for the CMP Camagüey site — template-level
overrides, Tabler CSS variables, a CMP Camagüey favicon and logo, and
per-instance theming — **without forking or editing Tabler**. Branding MUST be
driven by configuration so each deployment can carry its own identity without
code changes.

This proposal replaces the legacy `078 — tema-personalizado` framing (Spanish
only, mismatched change number, and an incorrect "`.dark` class" premise) with
a canonical OpenSpec change anchored to the current code.

## Scope

### In Scope

- A project brand override stylesheet built on Tabler CSS variables (`--tblr-*`),
  loaded after Tabler so the cascade wins without touching `tabler*.css`.
- A curated ocean-blue / coastal-green palette applied as the instance default.
- Dark mode adapted to the brand palette (not the bare Tabler inversion) via
  `[data-bs-theme="dark"]` variable overrides.
- CMP Camagüey favicon and primary logo.
- Per-instance theming via the existing DB-backed `SiteConfiguration` singleton,
  exposed to templates through a context processor.

### Out of Scope

- Forking or vendoring Tabler source, or editing `static/dist/css/tabler*.css`.
- Per-user theme persistence beyond the existing localStorage switcher
  (`settings.html` / `scripts.html`).
- Reworking individual component templates (buttons, badges, cards, navbar);
  they inherit the palette automatically through `--tblr-*` variables.
- Multi-tenant isolation beyond the single `SiteConfiguration` row.

## Approach

Grounded in the current code (read-only audit):

1. **Brand CSS variables, no fork.** Tabler exposes theming through CSS
   variables and `[data-bs-theme-primary]` / `[data-bs-theme-base]` attribute
   presets defined in `static/dist/css/tabler-themes.min.css` (e.g.
   `[data-bs-theme-primary=blue]{--tblr-primary:#066f…}`). Add
   `static/dist/css/theme.css` that re-declares a curated subset
   (`--tblr-primary`, `--tblr-primary-rgb`, `--tblr-link`, `--tblr-secondary`,
   and dark-tuned values under `[data-bs-theme="dark"]`). Link it in
   `templates/includes/base/head.html` immediately after `tabler.min.css`
   (after line 10) so the cascade wins without editing Tabler source.

2. **Per-instance theming via `SiteConfiguration`.** `apps/core/models.py:131`
   `SiteConfiguration` is a singleton (its `save()` at `:147` blocks a second
   row). Extend it with branding fields: `primary_color` (CharField hex),
   `theme_base` (CharField choices: slate/gray/zinc/neutral/stone),
   `brand_logo` (ImageField — MUST use `FileHandlerMixin` + `file_fields`),
   `favicon` (ImageField). Expose them through a new context processor
   registered alongside `apps.core.context_processors.menu_notifications`
   (`config/settings.py:139`). These values seed the `themeConfig` defaults
   currently hard-coded in `templates/includes/base/scripts.html:9-17`
   (`theme-primary:"blue"`, `theme-base:"gray"`), so the instance default
   renders server-side while the user switcher (`settings.html`) still overrides
   via localStorage.

3. **Favicon.** `templates/includes/base/head.html:6-8` points to
   `{% static '' %}dist/img/favicon.ico` (present at
   `static/dist/img/favicon.ico`). Ship the CMP Camagüey favicon at that path;
   when `SiteConfiguration.favicon` is set, the context processor overrides the
   `href`.

4. **Logo.** The brand mark lives in `templates/includes/logo.html` (inline
   SVG) and is rendered as `navbar-brand-image` in
   `templates/includes/home/navbar.html:16`,
   `templates/includes/dashboard/sidebar.html:17`, and
   `templates/includes/home/footer.html:70-86`. Keep the inline SVG as the
   default CMP/INSMET mark; when `SiteConfiguration.brand_logo` is set, render
   that asset instead.

5. **Dark mode brand adaptation.** Dark mode is already driven by
   `data-bs-theme="dark"` (`templates/includes/base/head.html:20-22`,
   `templates/includes/dashboard/sidebar.html:2`). Add brand-tuned `--tblr-*`
   overrides scoped to `[data-bs-theme="dark"]` in `theme.css` so dark mode uses
   the ocean palette rather than the default inversion.

6. **Static pipeline.** New CSS/asset files dropped into `static/` are collected
   automatically: `config/settings.py:263-270`
   (`STATICFILES_DIRS=[BASE_DIR/'static']`, WhiteNoise
   `CompressedManifestStaticFilesStorage` in prod). No build step or Tabler fork
   is required.

## Acceptance Criteria

- [ ] A project `static/dist/css/theme.css` exists and is linked after
      `tabler.min.css` in `templates/includes/base/head.html`.
- [ ] Brand palette is applied globally through `--tblr-*` variables; no edits
      to `tabler*.css`.
- [ ] Dark mode uses brand-tuned variables under `[data-bs-theme="dark"]`, not
      the default inversion.
- [ ] Favicon at `static/dist/img/favicon.ico` is the CMP Camagüey mark.
- [ ] Primary logo renders the CMP/INSMET brand mark in navbar, sidebar, and
      footer.
- [ ] `SiteConfiguration` exposes branding fields; a context processor injects
      them; `themeConfig` defaults are seeded from it.
- [ ] `djlint --reformat --check` passes on touched templates and
      `python manage.py check` is clean.
- [ ] No regression in existing Tabler components or the runtime theme switcher.

## Rollback

- Remove the `<link>` to `theme.css` from
  `templates/includes/base/head.html` and delete `static/dist/css/theme.css`.
- Revert the `SiteConfiguration` branding fields via `makemigrations` +
  `migrate` (or `migrate <app> <previous>`); remove the context processor entry
  from `config/settings.py:139`.
- Restore any replaced `favicon.ico` / logo assets from git history.
- No Tabler source was modified, so no vendor rollback is needed.
