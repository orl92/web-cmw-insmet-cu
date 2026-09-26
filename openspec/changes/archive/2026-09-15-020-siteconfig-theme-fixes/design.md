# Design — 020-siteconfig-theme-fixes

## Overview

Follow-up defect fix to 019. The theme switcher marks offcanvas radios but never renders
the model-seeded base on `<html>`; reset only re-sets radios; `theme.css` overrides
`--tblr-link`; `site/settings.html` bypasses the `layouts/form.html` standard. All work is
override wiring in project-owned files — no schema change, no migration, no Tabler fork,
vanilla JS.

## Current State (verified, read-only)

| Concern | Current reality | Evidence |
|---|---|---|
| Seed render | `DOMContentLoaded` only marks radios via `checkItems()`; never sets `data-bs-*` | `templates/includes/base/scripts.html:50-62,92-93` |
| Reset | removes attrs + clears `localStorage`, `applyTheme(model)`, then `checkItems()` — but `theme-base`/`theme-*` attrs are NOT re-applied, so base never renders | `scripts.html:79-91` |
| Change | switch `change` handler DOES set `data-bs-<key>` + `localStorage` correctly | `scripts.html:63-78` |
| Brand override | `theme.css` sets dark `--tblr-primary`/`--tblr-primary-rgb` **and** `--tblr-link: #2b4b9b` | `static/dist/css/theme.css:8-12` |
| Template | extends `layouts/dashboard.html`, manual `.card`, no `form_card` | `apps/core/templates/pages/core/site/settings.html:1-58` |
| Brand logo field | `ImageField(upload_to='brand/')`, clearable file input, no format hint | `apps/core/models.py:149-151`; `forms/site_configuration.py:19` |
| Favicon field | `ImageField`, bare `ClearableFileInput`, no preview | `models.py:152`; `forms/site_configuration.py:20` |
| Form shell/partials | `layouts/form.html` (extends dashboard, `{% block form %}`, multipart) + `form_card.html` sections | `templates/layouts/form.html:1-43`; `includes/dashboard/form_card.html:1-11` |

## Target State

1. **Seed + reset render the model.** New `applyConfig()` sets every `themeConfig` key as a
   `data-bs-<key>` attribute on `document.documentElement`. Called on `DOMContentLoaded`
   (seeds from model) and on `#reset-changes` (after clearing overrides, re-applies model).
2. **`theme.css` brand-only.** Drop `--tblr-link`; keep only dark `--tblr-primary`/`-rgb`
   (`#2b4b9b` / `43,75,155`).
3. **`settings.html` reworked** to `layouts/form.html` + `form_card` sections.
4. **`brand_logo` hint** + **favicon** preview card (mirrors `service/update.html`).

## Architecture Decisions

### Decision: `applyConfig()` renders all `themeConfig` keys as `data-bs-*` on `<html>`

**Choice**: Extract from `checkItems()` a function that BOTH marks radios AND sets every
`themeConfig` key as `data-bs-<key>` on `document.documentElement`, preferring
`localStorage['tabler-<key>']` when present, else the model value. `checkItems()` stays for
radio-only marking.

**Alternatives**: hand-edit each key at load (brittle); set only `theme-base` (inconsistent
with the generic `change` handler).
**Rationale**: One code path drives the switch and the seeded load — a seeded
`data-bs-theme-base` renders identically to a user-selected one (spec THEME-BASE-APPLIED /
RESET-RESTORES-MODEL), matching the existing `change` handler (`scripts.html:69`).

**Order of operations** (annotated):
```js
var applyConfig = function () {
  // 1. Priority: localStorage override -> model value (matches change handler read).
  for (var key in themeConfig) {
    var value = window.localStorage["tabler-" + key] || themeConfig[key];
    if (!!value) {
      document.documentElement.setAttribute("data-bs-" + key, value); // (b) render
    }
  }
  checkItems(); // (a) mark matching radios in offcanvas — unchanged behaviour
};
```
- **Seed**: `document.addEventListener("DOMContentLoaded", …)` calls
  `applyTheme(themeConfig["theme-primary"])` then `applyConfig()`.
- **Change** (existing `scripts.html:63-78`, unchanged): sets `data-bs-<key>` +
  `localStorage` atomically, then updates `url` query; `theme-primary` also calls
  `applyTheme()`.
- **Reset** (`#reset-changes`): remove each `data-bs-<key>` attr, each
  `localStorage['tabler-<key>']`, remove the inline `--tblr-primary`/`--tblr-primary-rgb`,
  delete url params, then `applyTheme(themeConfig["theme-primary"])` (model primary) and
  `applyConfig()` (re-seeds model base + marks radios). This satisfies
  RESET-RESTORES-MODEL: localStorage is cleared BEFORE `applyConfig()` reads it, so
  `applyConfig()` falls back to the model.

**Why seed re-applies on load (intended)**: a visitor who previously chose a swatch has
that choice in `localStorage`, so `applyConfig()` renders their override (per fixed
`localStorage` semantics, scenario "Stored override wins"). A fresh visitor has no entry →
model wins (scenario "Model base renders").

### Decision: `data-bs-theme` vs `data-bs-theme-base`

`tabler-themes.min.css` keys its *scheme* (light/dark) presets on `[data-bs-theme]` and its
*base swatch* on `[data-bs-theme-base]`. `themeConfig.theme-base` renders
`data-bs-theme-base="<model>"` so the correct base palette applies; `themeConfig.theme`
("light") renders `data-bs-theme="light"` (or the user's dark choice). `theme.css`'s dark
block only overrides primary under `[data-bs-theme="dark"]`, so it composes cleanly with
any base. `applyTheme()` separately sets `data-bs-theme-primary` (preset) + inline
`--tblr-primary`/`--tblr-primary-rgb` (wins cascade for light primary per model).

**Alternatives**: drop base attr (regresses base palette); merge base into `theme`
(overloads scheme, breaks Tabler preset matching).
**Rationale**: keeps Tabler's two-axis theming (scheme × base) intact — the same mechanism
as the working `change` handler.

### Decision: `theme.css` removes only `--tblr-link`

**Choice**: `static/dist/css/theme.css` final content, under `[data-bs-theme="dark"]`:
`--tblr-primary: #2b4b9b; --tblr-primary-rgb: 43, 75, 155;` — no `--tblr-link`. Light primary
stays runtime (scripts.html). No other overrides exist today (verified: only lines 9-11).

**Alternatives**: keep `--tblr-link` (violates spec THEME-CSS-PRIMARY-ONLY and the user's
"solo primary"); hardcode light primary in `theme.css` (loses per-instance authority).
**Rationale**: Link color should inherit Tabler default in both schemes; the project logo
(`#2b4b9b`/`#e5201e`) is unaffected because link styling is separate.

### Decision: favicon/brand reuse `service/update.html` image pattern

**Choice**: Markup for both image fields mirrors `service/update.html:140-180`: a card with
a 64px square `avatar` preview + "Ver imagen actual" fslightbox `<a data-fslightbox>` +
file input; `accept` hints. Favicon uses a `rounded` (square) 64px preview; `brand_logo` a
plain labeled hint (no preview needed per scope, stays default inline SVG when unset).

**Alternatives**: bare `ClearableFileInput` (current — no feedback, violates
SETTINGS-FORM-STANDARD); heavy custom uploader (out of scope).
**Rationale**: reuses the project's established, tested partial pattern; fslightbox already
loaded by `layouts/form.html:41`.

## Data Flow

```
DOMContentLoaded
  └─ applyTheme(model primary) → <html style="--tblr-primary…">+ data-bs-theme-primary
  └─ applyConfig() → <html data-bs-theme-base="…"> … data-bs-<every key> + radios checked
        (value = localStorage override ?? model)
switcher change ──► set data-bs-<key> + tabler-<key> ──► (theme-primary) applyTheme(hex)
reset ──► remove attrs + clear localStorage + remove inline vars
        ──► applyTheme(model primary) + applyConfig()   // re-seeds model
```

## Files to Change

| File | Action | Description |
|---|---|---|
| `templates/includes/base/scripts.html` | Modify | add `applyConfig()` (sets `data-bs-*` + `checkItems()`); seed calls it; reset re-applies it |
| `static/dist/css/theme.css` | Modify | remove `--tblr-link`; keep only dark primary/rgb |
| `apps/core/templates/pages/core/site/settings.html` | Modify | extend `layouts/form.html`; `{% block form %}`; `form_card` sections; brand_logo hint; favicon preview card |

## Interfaces / Contracts

- `applyConfig()` — no args; closure over `themeConfig`, `form`. Returns nothing.
- Settings template: `{% extends 'layouts/form.html' %}`, `{% block form %}` containing
  section cards:
  - `include 'includes/dashboard/form_card.html' with card_title='Colores y tema'` →
    `primary_color` + `theme_base` side by side (`col-md-6` each, hex/choices preserved).
  - `include ... with card_title='Identidad'` → `brand_logo` hint + `favicon` preview card.
  - `enctype="multipart/form-data"` and `novalidate` come from the base layout
    (`form.html:12-14`), so no change needed.
- Favicon markup (mirrors `service/update.html:140-180`), using `object.favicon` (the
  UpdateView object):
```django
<div class="mb-3">
  <label class="form-label" for="{{ form.favicon.id_for_label }}">{{ form.favicon.label }}</label>
  <div class="card"><div class="card-body">
    <div class="d-flex align-items-center">
      <div class="me-3">
        <div class="avatar avatar-xl rounded" style="width:64px;height:64px;overflow:hidden">
          {% if object.favicon %}
            <img src="{{ object.favicon.url }}" alt="Favicon"
                 style="width:100%;height:100%;object-fit:cover">
          {% endif %}
        </div>
      </div>
      <div class="flex-grow-1">
        {{ form.favicon|with_invalid }}
        {% if form.favicon.errors %}<div class="invalid-feedback d-block">{{ form.favicon.errors.0 }}</div>{% endif %}
        <small class="text-muted">Formatos: JPG, PNG, GIF. No se admiten SVG. Dejar en blanco si no desea cambiar el favicon actual.</small>
        {% if object.favicon %}
          <a data-fslightbox="gallery" href="{{ object.favicon.url }}" class="btn btn-outline-primary btn-sm mt-2">
            <i class="icon ti ti-eye"></i> Ver imagen actual
          </a>
        {% endif %}
      </div>
    </div>
  </div></div>
</div>
```
- `brand_logo` hint: `Formatos: JPG, PNG, GIF. No se admiten SVG. Dejar en blanco si no desea cambiar el logo actual.`

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Static | templates parse & format | `djlint . --reformat --check` on touched templates |
| Django | `manage.py check` + `apps.core` tests | `python manage.py test apps.core` (regression suite for policies/fields) |
| Manual smoke | seed/render/reset/override | browser checklist below |

JS has **no browser harness** (Django + vanilla, no Node/bundler). Verification is
structural (read the diff against `applyConfig()` contract) plus manual browser steps:

- Fresh visitor → `<html data-bs-theme-base="<model>">` + radio checked.
- Reset → attrs removed, `localStorage` cleared, model base+primary re-applied, radios model.
- Pick a swatch (e.g. green) → reload → override still wins (localStorage).
- `theme.css` inspected → only dark `--tblr-primary`/`-rgb`; link color = Tabler default.
- Edit page renders two `form_card` sections; favicon shows preview + lightbox when set.

## Threat Matrix

N/A — no routing change (URL/view already exist), no shell/subprocess, no VCS/PR
automation, no executable classification, no process integration. JS is purely
client-side attribute/`localStorage` manipulation; no server command execution.

## Migration / Rollout

No migration required — no model or schema change. Rollback: restore `scripts.html`,
`theme.css`, `settings.html` from git (all additive/override edits).

## Open Questions

- [ ] Confirm fslightbox gallery name (`gallery`) is acceptable for sharing the favicon
      lightbox with any other fslightbox groups on the edit page (if collision, use a
      distinct group id).
