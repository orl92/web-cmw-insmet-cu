# Design — 019-siteconfig-website

## Overview

Extends 007-tema-personalizado (which shipped the `SiteConfiguration` branding fields,
`site_branding` context processor, and `theme.css`) by (1) exposing web editing of the
singleton and (2) making `primary_color` actually render. The crux: Tabler 1.4 presets in
`tabler-themes.min.css` only match **named** swatches, so the hex `data-bs-theme-primary`
seeded in `scripts.html` matches no preset and the green/teal named swatches win. All work
is *override wiring in project-owned files* — no Tabler fork, no bundlers, vanilla JS.

## Current State (verified, read-only)

| Concern | Current reality | Evidence |
|---|---|---|
| Web edit | Not present; admin only | no `SiteConfigurationUpdateView`, no `core:*siteconfig*` URL |
| Source of render | `theme.css` hardcodes `:root{--tblr-primary:#0b6e99}` + green `--tblr-secondary:#1a8a5c` | `static/dist/css/theme.css:7-12` |
| Seed | model hex into `themeConfig.theme-primary` only | `templates/includes/base/scripts.html:14` |
| Change | sets `data-bs-theme-primary=value`; hex matches NO preset | `scripts.html:39`; `tabler-themes.min.css` named-only presets |
| User override | named swatch `green`/`teal` matches preset → wins over model | `templates/includes/base/settings.html:130-147` |
| Default color | `primary_color` default `#0b6e99` | `apps/core/models.py:145` |
| Context proc | `site_branding` returns singleton | `apps/core/context_processors.py:11` |
| Singleton save | block duplicate; `get_instance()` default row | `apps/core/models.py:170-180` |

## Target State

1. **Edit page** mirroring `CompanySettingsUpdateView`
   (`apps/core/views/company_settings.py:15`): `SiteConfigurationUpdateView` with
   `LoginRequiredMixin + PermissionRequiredMixin`, `permission_required =
   'core.change_siteconfiguration'`, singleton `get_object()`, `log_action`
   (`apps.core.utils:46`), `messages.success`, `reverse_lazy('core:site_configuration')`.
   `SiteConfigurationForm` ModelForm with hex-validated `primary_color`, `theme_base`,
   `brand_logo`, `favicon` (FileHandlerMixin/file_fields already on model, `models.py:154`).
   Template `pages/core/site/settings.html` with `enctype="multipart/form-data"`; route
   `configuracion-sitio/` (`core:site_configuration`); link in the Config menu beside
   "Empresa".
2. **Color truth shift.** Change default `#0b6e99 → #2b4b9b` (`models.py:145`) + a
   gitignored migration data-updating the existing row.
3. **Hex→CSS rendering** (crux, below).
4. **theme.css reconciliation** (below).

## Architecture Decisions

### Decision: Render the model hex as inline CSS variables

**Choice**: In `scripts.html`, on load seed and in `applyTheme` also set
`--tblr-primary`/`--tblr-primary-rgb` on `document.documentElement.style` via a hex→rgb
helper. On the theme switcher `change`, resolve the chosen value to hex, set
`data-bs-theme-primary` (Tabler preset for named swatches AND for the model hex) **and**
the same `--tblr-*` inline vars. Inline `style` beats `:root` in `theme.css`.

**Alternatives**: keep only `data-bs-theme-primary` (proved broken); fork Tabler (banned);
hardcode in `theme.css` (loses per-instance authority).
**Rationale**: Inline element style has highest cascade specificity after `!important`;
`--tblr-primary-rgb` must be set too because Tabler alpha utilities (buttons, shadows) use
it as `rgb(var(--tblr-primary-rgb))`. No build step needed.

**Hex→rgb helper** (vanilla):
```js
function hexToRgb(hex){hex=hex.replace('#','');var n=parseInt(hex,16);
  return (n>>16&255)+','+(n>>8&255)+','+(n&255);}
```

### Decision: Named→hex mapping on the switcher

**Choice**: A small JS map `{blue:'#066f…', green:'#5eba00', teal:'#20c997', …}` covering the
12 swatch values in `settings.html`, so named choices set real `--tblr-*` vars.
**Alternatives**: compute the preset's rgb from `tabler-themes.min.css` (fragile parsing);
let named swatches only set `data-bs-theme-primary` (reenables the bug — preset wins but the
model hex is unknown).
**Rationale**: Deterministic, trivially auditable against `settings.html:50-156`; keeps Tabler
preset behavior and localStorage semantics intact.

### Decision: Reset re-applies the model, not theme.css

**Choice**: `#reset-changes` removes the `data-bs-*` attrs **and** the inline `--tblr-*`
vars, clears `tabler-*` localStorage, then calls `applyTheme(modelHex)`.
**Rationale**: Without a re-apply, clearing vars falls back to `theme.css` `:root`
(`#0b6e99`) — wrong. Re-applying the seeded model hex guarantees "reset = model" per
`PRIMARY-COLOR-AUTHORITATIVE`.

### Decision: theme.css secondary handling

**Choice**: Remove hardcoded `--tblr-secondary:#1a8a5c` (light) and `#28a745` (dark); let
Tabler's neutral secondary default stand. Keep brand-tuned dark primary tuned to `#2b4b9b`.
**Alternatives**: tie `--tblr-secondary` to the model hex (adds a second color authority the
model doesn't model); keep green (conflicts — the reported bug).
**Rationale**: The model exposes only `primary_color`; deriving a harmonized secondary from
blue is over-reach and green is off-mark (`#2b4b9b`/`#e5201e` identity in `logo.html`).
Leaving Tabler's default is neutral, regress-free.

### Decision: Default + data migration

**Choice**: Change `default` to `'#2b4b9b'`; a gitignored migration runs an `Update` data
migration on the singleton row (project: migrations not versioned).
**Rationale**: Fresh installs and existing rows converge; matches `0001_initial` + the
gitignore convention.

## Data Flow

```
SiteConfigurationUpdateView → form.save() → SiteConfiguration singleton
        → log_action + messages → reverse_lazy('core:site_configuration')
site_branding context_processor → scripts.html themeConfig + inline --tblr-*
   └─ model hex (#2b4b9b) → applyTheme() → <html style="--tblr-primary:…;--tblr-primary-rgb:…">
switcher change (named) → map<named→hex> → applyTheme(hex) → same inline vars + localStorage
reset → remove attrs/vars + clear localStorage → applyTheme(modelHex)
```

## Files to Change

| File | Action | Description |
|---|---|---|
| `apps/core/views/site_configuration.py` | Create | `SiteConfigurationUpdateView` (mirror company_settings.py) |
| `apps/core/views/__init__.py` | Modify | import/export the view |
| `apps/core/forms/site_configuration.py` | Create | `SiteConfigurationForm` (hex `primary_color`, `theme_base`, `brand_logo`, `favicon`) |
| `apps/core/urls.py` | Modify | `configuracion-sitio/` → `core:site_configuration` |
| `apps/core/templates/pages/core/site/settings.html` | Create | multipart form (mirror company/settings.html) |
| `templates/includes/dashboard/menu/_configuracion.html` | Modify | add "Sitio" link + `'site' in segment` active/show; gate on `change_siteconfiguration` |
| `templates/includes/base/scripts.html` | Modify | hex→rgb helper, `applyTheme()`, seed+change+reset wiring |
| `static/dist/css/theme.css` | Modify | drop `#0b6e99` primary + green secondary; keep dark tuned to `#2b4b9b` |
| `apps/core/models.py` | Modify | default `#0b6e99 → #2b4b9b` |
| `apps/core/migrations/*` | Create | generated + data update (gitignored) |
| `apps/core/tests/test_site_configuration_views.py` | Create | view/form tests |
| `apps/core/tests/test_site_configuration_branding.py` | Modify | default assertion `#0b6e99 → #2b4b9b` |

## Interfaces / Contracts

- `SiteConfigurationUpdateView`: `LoginRequiredMixin, PermissionRequiredMixin`,
  `permission_required='core.change_siteconfiguration'`, `UpdateView`, singleton
  `get_object()`, `success_url=reverse_lazy('core:site_configuration')`.
- `SiteConfigurationForm.clean_primary_color`: MUST match `^#[0-9a-fA-F]{6}$` else
  `ValidationError` (SHALL NOT persist).

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | hex→rgb helper | assert `hexToRgb('#2b4b9b') === '43,75,155'` (extractable or inline-asserted) |
| Unit/Form | hex validation, `theme_base` choices | mirror `test_company_settings_forms.py` |
| Integration | view: 302 anon, 403 no-perm, 200/redirect with `change_siteconfiguration`, singleton persists | mirror `test_company_settings_views.py` |
| Integration | migration data update | after `migrate`, row `primary_color == '#2b4b9b'` |
| Regression | default assertion | update `test_site_configuration_branding.py:9` |

## Threat Matrix

N/A — no routing boundary change (only a new static URL + view), no shell/subprocess, no
VCS/PR automation, no executable classification, no process integration. JS is entirely
client-side inline styling; no server command execution.

## Migration / Rollout

- Gitignored migration: schema default change + `RunPython`/`RunSQL` update of the singleton
  row to `#2b4b9b`. Rollback: `migrate core <prev>`; restore `theme.css`, `scripts.html`,
  `settings.html`, view/form/template/URL from git.

## Open Questions

- [ ] Confirm exact hex values for the 12 named-swatch map entries
      (`#066f…`, `#5eba00`, `#20c997`, …) against `tabler-themes.min.css` during apply.
