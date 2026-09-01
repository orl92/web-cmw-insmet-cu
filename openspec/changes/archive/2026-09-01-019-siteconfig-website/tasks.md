# Tasks: 019-siteconfig-website — SiteConfiguration Web Edit & Color Truth

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

## Phase 1: Model Default & Regression Baseline

- [x] 1.1 RED: `test_site_configuration_branding.py:9` — assert default `'#2b4b9b'` (fails)
- [x] 1.2 Change `apps/core/models.py:145` default `'#0b6e99'` → `'#2b4b9b'`
- [x] 1.3 `makemigrations core` + data migration (`RunPython`) updating singleton row
- [x] 1.4 GREEN: `python manage.py test apps.core` branding passes

## Phase 2: Form & View (TDD)

- [x] 2.1 RED: `test_site_configuration_forms.py` — valid hex accepts, `"red"`/`"#12345"`/`"#1234567"` reject
- [x] 2.2 Create `apps/core/forms/site_configuration.py` — `SiteConfigurationForm(ModelForm)`: fields `primary_color` (color widget), `theme_base`, `brand_logo`, `favicon`; `clean_primary_color` hex regex `^#[0-9a-fA-F]{6}$`
- [x] 2.3 GREEN: form tests pass
- [x] 2.4 RED: `test_site_configuration_views.py` — anon→302, no-perm→403, with-perm GET→200, POST valid→302+singleton updated
- [x] 2.5 Create `apps/core/views/site_configuration.py` — `SiteConfigurationUpdateView` mirroring `company_settings.py`: `permission_required='core.change_siteconfiguration'`, singleton `get_object()`, `log_action`, `messages.success`
- [x] 2.6 Update `apps/core/views/__init__.py` — import/export view
- [x] 2.7 GREEN: view tests pass

## Phase 3: URL Route & Template

- [x] 3.1 Add URL `configuracion-sitio/` → `core:site_configuration` in `apps/core/urls.py`
- [x] 3.2 Create `apps/core/templates/pages/core/site/settings.html` — extend `layouts/dashboard.html`, `enctype="multipart/form-data"`, fields: `primary_color`, `theme_base`, `brand_logo`, `favicon`; mirror `pages/core/company/settings.html`
- [x] 3.3 `djlint .../site/settings.html --reformat --check`

## Phase 4: Menu Integration

- [x] 4.1 Modify `_configuracion.html` — add `change_siteconfiguration` perm gate, "Sitio" item linking `core:site_configuration`, `'site' in segment` active condition

## Phase 5: JS Theme Wiring

- [x] 5.1 Modify `scripts.html` — add `hexToRgb()` helper, `applyTheme(hex)` setting `data-bs-theme-primary` + inline `--tblr-primary`/`--tblr-primary-rgb` on `documentElement.style`
- [x] 5.2 Seed: `applyTheme(themeConfig["theme-primary"])` on load; named→hex swatch map on switcher `change`
- [x] 5.3 Reset handler: remove inline vars, clear localStorage, `applyTheme(modelHex)`

## Phase 6: CSS Reconciliation

- [x] 6.1 Modify `theme.css` — remove `--tblr-primary`/`--tblr-primary-rgb`/`--tblr-link` from `:root`, remove green `--tblr-secondary` from `:root` and dark; keep dark primary tuned `#2b4b9b`

## Phase 7: Verification

- [x] 7.1 `python manage.py check` — no errors
- [x] 7.2 `python manage.py test apps.core` — full suite passes
- [x] 7.3 `djlint .../site/settings.html --reformat --check` passes
- [x] 7.4 Verify `logo.html` + `logo.svg` unmodified

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~200–280 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low
