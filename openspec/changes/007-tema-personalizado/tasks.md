# Tasks — 007-tema-personalizado

## Phase 1 — Brand CSS override (no fork)

- [ ] Create `static/dist/css/theme.css` with `:root` `--tblr-*` overrides
      (ocean-blue / coastal-green palette: primary, primary-rgb, link, secondary).
- [ ] Add a `[data-bs-theme="dark"]` block in `theme.css` with dark-tuned
      brand variables.
- [ ] Link `theme.css` in `templates/includes/base/head.html` immediately after
      `tabler.min.css` (after line 10).

## Phase 2 — Per-instance branding model

- [ ] Add `primary_color`, `theme_base`, `brand_logo`, `favicon` fields to
      `SiteConfiguration` in `apps/core/models.py:131`.
- [ ] Make `SiteConfiguration` inherit `FileHandlerMixin` (`apps/core/models.py:25`)
      and declare `file_fields = ['brand_logo', 'favicon']`.
- [ ] Keep `default_permissions = ()` and add the 4 Spanish custom permissions.
- [ ] Generate migration: `python manage.py makemigrations core`.

## Phase 3 — Context processor + template wiring

- [ ] Add `site_branding(request)` to `apps/core/context_processors.py`
      returning the `SiteConfiguration` singleton.
- [ ] Register `apps.core.context_processors.site_branding` in
      `config/settings.py:139`.
- [ ] Make favicon `href` in `templates/includes/base/head.html:6-8` use
      `{{ site_branding.favicon.url }}` when present.
- [ ] Render `{{ site_branding.brand_logo.url }}` in `templates/includes/logo.html`
      (fallback to inline SVG) and reuse in `home/navbar.html:16`,
      `dashboard/sidebar.html:17`, `home/footer.html:70-86`.
- [ ] Seed `themeConfig` defaults (`theme-primary` / `theme-base`) in
      `templates/includes/base/scripts.html:9-17` from the context processor
      instead of hard-coded `blue` / `gray`.

## Phase 4 — Assets & verification

- [ ] Ship CMP Camagüey `favicon.ico` at `static/dist/img/favicon.ico`.
- [ ] Confirm brand logo asset (or keep inline SVG default).
- [ ] Run `python manage.py check`.
- [ ] Run `python manage.py test apps.core`.
- [ ] Run `djlint templates/includes/base/head.html templates/includes/logo.html --reformat --check`.
- [ ] Manual UI pass: palette, dark mode, favicon, logo, and per-instance
      re-theme via `SiteConfiguration`.
