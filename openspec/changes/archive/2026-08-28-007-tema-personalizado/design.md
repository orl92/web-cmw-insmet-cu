# Design — 007-tema-personalizado

## Overview

The site already ships Tabler 1.4.0 bundled locally (not via CDN) and already
ships a runtime theme switcher. The work is therefore *configuration and
override*, not forking:

- Tabler theming is attribute- and variable-driven
  (`[data-bs-theme-primary]`, `[data-bs-theme-base]`, `--tblr-*`), all defined
  in `static/dist/css/tabler-themes.min.css`. We override a curated subset in a
  new `theme.css` loaded after `tabler.min.css`.
- The runtime switcher (`templates/includes/base/settings.html` +
  `templates/includes/base/scripts.html`) persists user choices in
  `localStorage` under `tabler-*` keys. We only change the *server-rendered
  defaults*, not the switcher behavior.
- Per-instance identity lives in `SiteConfiguration` (`apps/core/models.py:131`),
  the project's existing singleton config home, surfaced via a context
  processor next to `apps.core.context_processors.menu_notifications`
  (`config/settings.py:139`).

## Current State (verified, read-only)

| Concern | Current reality | Evidence |
|---|---|---|
| Tabler CSS | Bundled locally, not forked | `templates/includes/base/head.html:10-12`; files in `static/dist/css/` |
| Theme presets | Attribute-driven `--tblr-*` via `tabler-themes.min.css` | `static/dist/css/tabler-themes.min.css` (`[data-bs-theme-primary=blue]{--tblr-primary:#066f…}`) |
| Default theme | `theme-primary:"blue"`, `theme-base:"gray"` | `templates/includes/base/scripts.html:9-17` |
| User switcher | Offcanvas "Configuración del tema" | `templates/includes/base/settings.html:1` |
| Dark mode | `data-bs-theme="dark"` attribute | `templates/includes/base/head.html:20-22`; `templates/includes/dashboard/sidebar.html:2` |
| Favicon | `{% static '' %}dist/img/favicon.ico` | `templates/includes/base/head.html:6-8`; asset present |
| Logo | Inline SVG in `includes/logo.html` | `templates/includes/home/navbar.html:16`; `dashboard/sidebar.html:17`; `home/footer.html:70-86` |
| Per-instance config | `SiteConfiguration` singleton, NO branding fields yet | `apps/core/models.py:131-150` |
| Static collection | `STATICFILES_DIRS=[BASE_DIR/'static']` + WhiteNoise | `config/settings.py:263-270` |
| Global brand CSS | Does NOT exist | `static/dist/css/` has only `dashboard/forecast/utils/pdf-*` |

## Target State

1. **`static/dist/css/theme.css`** — project brand overrides.
   - `:root` block re-declaring `--tblr-primary`, `--tblr-primary-rgb`,
     `--tblr-link`, `--tblr-secondary` with the ocean-blue / coastal-green
     palette.
   - `[data-bs-theme="dark"]` block re-declaring the same variables with
     dark-tuned values (so dark mode is brand-aware, not the default inversion).
   - Loaded in `templates/includes/base/head.html` **after** line 10
     (`tabler.min.css`) so it wins via cascade specificity/order.

2. **`SiteConfiguration` branding fields** (`apps/core/models.py:131`):
   - `primary_color` — `CharField(max_length=7, default='#0b6e99')` (ocean blue).
   - `theme_base` — `CharField` with `choices` slate/gray/zinc/neutral/stone,
     default `gray`.
   - `brand_logo` — `ImageField`; the model MUST inherit `FileHandlerMixin`
     (`apps/core/models.py:25`) and declare `file_fields = ['brand_logo',
     'favicon']`.
   - `favicon` — `ImageField` (same mixin requirement).
   - `default_permissions = ()` + the 4 Spanish custom permissions
     (`view_*`/`add_*`/`change_*`/`delete_*`) per project convention.

3. **Context processor** `apps/core/context_processors.py` — new
   `site_branding(request)` returning the `SiteConfiguration` singleton
   (via `get_instance()`-style access), registered in
   `config/settings.py:139`.

4. **Template wiring**:
   - `head.html`: add `<link rel="stylesheet" href="{% static 'dist/css/theme.css' %}">`
     after `tabler.min.css`; favicon `href` switches to
     `{{ site_branding.favicon.url }}` when present.
   - `logo.html` / navbar+sidebar+footer: render `{{ site_branding.brand_logo.url }}`
     when set, otherwise the inline SVG default.
   - `scripts.html`: seed `themeConfig` `theme-primary` / `theme-base` from the
     context processor values instead of the hard-coded `blue` / `gray`.

## Data Model (delta)

```python
# apps/core/models.py — SiteConfiguration (extends existing singleton)
class SiteConfiguration(models.Model):
    # ... existing: uuid, maintenance_mode ...
    primary_color = models.CharField(max_length=7, default='#0b6e99',
                                     verbose_name='Color primario')
    theme_base = models.CharField(max_length=10, choices=[...], default='gray',
                                  verbose_name='Base del tema')
    brand_logo = models.ImageField(upload_to='brand/', null=True, blank=True,
                                   verbose_name='Logo de marca')
    favicon = models.ImageField(upload_to='brand/', null=True, blank=True,
                                verbose_name='Favicon')
    # FileHandlerMixin + file_fields = ['brand_logo', 'favicon']
```

## Files to Change

- `static/dist/css/theme.css` — **new** brand override stylesheet.
- `templates/includes/base/head.html` — link `theme.css`; conditional favicon.
- `templates/includes/logo.html` + `home/navbar.html` + `dashboard/sidebar.html`
  + `home/footer.html` — conditional brand logo.
- `templates/includes/base/scripts.html` — seed `themeConfig` from context.
- `apps/core/models.py` — `SiteConfiguration` branding fields + mixin.
- `apps/core/context_processors.py` — new `site_branding`.
- `config/settings.py` — register context processor (`:139`).
- `apps/core/migrations/` — new migration (generated, not versioned).

## Constraints & Conventions

- Tabler source (`static/dist/css/tabler*.css`) MUST NOT be edited.
- Any model with `ImageField` MUST use `FileHandlerMixin` + `file_fields`.
- `default_permissions = ()` + 4 custom Spanish permissions on the model.
- Templates formatted with djlint (2-space indent); `*/emails/` excluded.
- Migrations generated and NOT committed (`.gitignore`).

## Verification

- `python manage.py check`
- `python manage.py test apps.core`
- `djlint templates/includes/base/head.html templates/includes/logo.html --reformat --check`
- Manual: load site → palette is ocean-blue; toggle dark mode → brand-tuned
  dark; favicon + logo are CMP Camagüey; changing `SiteConfiguration` re-themes
  without code edits.
