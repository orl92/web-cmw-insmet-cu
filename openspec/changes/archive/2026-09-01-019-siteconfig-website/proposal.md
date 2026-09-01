# Proposal

## Intent

Close the branding gap left by 007-tema-personalizado (scoped OUT there): a
web edit page for `SiteConfiguration` — today editable only in Django admin —
and making the model the authoritative source of the site's persistent color.

The model's `primary_color` (default `#0b6e99`, `apps/core/models.py:145`)
cannot render today: `scripts.html:14` seeds the hex into `themeConfig`, but
`tabler-themes.min.css` only defines **named** swatch presets; `theme.css`
hardcodes `--tblr-primary:#0b6e99` and loads before it (`head.html:16-18`); the
switcher's named swatches load later and win. So the button's `green`/`teal`
override the model — exactly what the user rejects.

The CMP logo identity (`#2b4b9b` / `#e5201e` in `templates/includes/logo.html`)
SHALL stay fixed; `navbar-brand-autodark` already handles dark mode.

## Scope

### In Scope

- Web edit page for `SiteConfiguration` mirroring the
  `CompanySettingsUpdateView` pattern (`apps/core/views/company_settings.py`,
  `apps/core/forms/company_settings.py`, template
  `pages/core/company/settings.html`, `apps/core/urls.py:18`).
- `core.change_siteconfiguration` via `LoginRequiredMixin` +
  `PermissionRequiredMixin`; route `configuracion-sitio/`; multipart form for
  `brand_logo`/`favicon` (`FileHandlerMixin` already on the model, `:154`).
- `primary_color` default → `#2b4b9b` + singleton row data update (local
  migration, gitignored per project).
- Theme button seeds from `site_branding.primary_color`; "Restablecer" returns
  to the model value; `green`/`teal` swatches never become the site's
  persistent color (visitor-local localStorage override stays).
- Reconcile `static/dist/css/theme.css`: drop hardcoded `#0b6e99` primary and
  green `--tblr-secondary` (`#1a8a5c` / `#28a745`) conflicting with the model.

### Out of Scope

- Changing logo colors or `static/dist/img/logo.svg`.
- Removing per-user theme persistence (localStorage).
- Multi-tenant or per-role branding.
- A hex color picker inside the switcher (hex stays on the edit page).

## Approach

1. **Edit page.** Add `SiteConfigurationUpdateView` mirroring
   `CompanySettingsUpdateView` (singleton `get_object()`, `log_action`,
   `messages.success`), a `SiteConfigurationForm` ModelForm (hex-validated
   `primary_color`, `theme_base`, `brand_logo`, `favicon`,
   `enctype="multipart/form-data"`), template under
   `pages/core/site/settings.html`, URL `configuracion-sitio/` in
   `apps/core/urls.py`. Saves go to the singleton the `site_branding` context
   processor reads (`apps/core/context_processors.py:11`).
2. **Truth shift.** Change `primary_color` default to `#2b4b9b`;
   `scripts.html` applies the seeded hex as the CSS variable — not only a
   `data-bs-theme-primary` attribute, which matches no preset — so the model
   color renders on first load; reset clears localStorage and re-applies it.
3. **Switcher.** Swatch radios stay a visitor-local override; `green`/`teal`
   no longer collide with the authority because the seeded value wins on load
   and reset.
4. **theme.css.** Remove conflicting hardcoded primary/green secondary; keep
   dark-mode brand tuning consistent with `#2b4b9b`.

## Acceptance Criteria

- [ ] `configuracion-sitio/` renders for users with
      `core.change_siteconfiguration`, denies others; edits persist to the singleton.
- [ ] `primary_color` default is `#2b4b9b`; a fresh visitor renders it.
- [ ] Theme button seeds from the model; reset restores it; a picked
      green/teal swatch never persists site-wide.
- [ ] `theme.css` no longer hardcodes `#0b6e99` or green secondary values.
- [ ] `logo.html` / `logo.svg` colors untouched.
- [ ] `python manage.py check`, `python manage.py test apps.core`, and
      `djlint --reformat --check` pass on touched templates.

## Rollback

- Revert the `primary_color` default change and data update via the gitignored
  migration (`makemigrations` reverse or `migrate core <prev>`).
- Restore `theme.css` and `scripts.html`/`settings.html` from git.
- Remove the URL/view/form/template additions — nothing else depends on them.
- No Tabler source, logo asset, or vendored file is modified.