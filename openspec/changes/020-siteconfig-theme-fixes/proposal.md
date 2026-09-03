# Proposal: 020 — Site config & theme fixes

## Intent

Follow-up to 019 (site-config website). Users report real defects in the
shipped theme/editing surface. Fix 4 correctness/UX gaps with no new
capabilities.

## Scope

### In Scope

1. **`theme_base` render fix** (`templates/includes/base/scripts.html`).
   `checkItems()` only marks radios from `themeConfig`; it never applies the
   `data-bs-*` attrs to `<html>`, so model-seeded base (`data-bs-theme-base`)
   never renders, and reset marks the radio without applying. Fix: on
   `DOMContentLoaded` and on reset, set **all** `themeConfig` values as
   `data-bs-*` attributes on `document.documentElement` (not just radios);
   reset clears localStorage, removes attrs, then re-applies from the model.
   `applyTheme` stays for primary.
2. **`theme.css` brand-only** (`static/dist/css/theme.css`). Currently only
   `--tblr-primary`/`--tblr-primary-rgb`/`--tblr-link` under dark. Per user
   ("solo primary, el resto como en tabler") drop `--tblr-link` override so
   light/dark default to Tabler; keep only dark `--tblr-primary`/`-rgb`
   (`#2b4b9b`); light primary stays runtime model (scripts.html).
3. **`site/settings.html` → `layouts/form.html`**
   (`apps/core/templates/pages/core/site/settings.html`). Rebuild extending
   `layouts/form.html` with `{% include 'includes/dashboard/form_card.html' %}`
   sections and `{% block form %}` (project standard, like
   `service/update.html`).
4. **`brand_logo` format hint** — clarify accepted formats (JPG/PNG/GIF only;
   no SVG — PIL rejects it). Keep the field. Default inline SVG in
   `templates/includes/logo.html` unchanged when unset.
5. **`favicon` image-design pattern** — mirror `service/update.html` image card
   (preview avatar + "Ver imagen actual" link), not a bare input.
6. **Housekeeping: Engram Django-version stale note (5.1.4→5.2.17).**
   OOS — handled directly by the orchestrator, NOT part of this SDD change.

### Out of Scope

- Removing per-user theme persistence (localStorage).
- Changing `logo.html` / logo identity or a hex picker in the switcher.
- New base/font/radius options or multi-tenant branding.
- `theme.css` light-primary hardcode (stays runtime model authority).
- Any Engram memory updates.

## Approach

Minimal, project-owned-file-only, vanilla JS. In `scripts.html` extract a
`applyConfig()` that (a) marks radios and (b) sets every `themeConfig` key as a
`data-bs-*` HTML-attr; call it on load and reset. Reset additionally removes
attrs + clears `localStorage` first, then re-applies model. `theme.css` edits
only remove `--tblr-link`. Template rework is pure markup following
`service/update.html`/`form_card.html`.

## Acceptance Criteria

- [ ] A visitor loads the site; `data-bs-theme-base` with the model value is on `<html>` (not only the radio).
- [ ] Clicking "Restablecer" clears localStorage, removes `data-bs-*`, and applies the model base + primary; radios reflect the model.
- [ ] `theme.css` sets only dark `--tblr-primary`/`-rgb`; `--tblr-link` reverted to Tabler default.
- [ ] `site/settings.html` extends `layouts/form.html`; `brand_logo` shows JPG/PNG/GIF (no SVG) hint; `favicon` shows preview + current-image link.
- [ ] `python manage.py check`, `python manage.py test apps.core`, and `djlint --reformat --check` pass on touched templates.

## Rollback

- Restore `scripts.html`, `theme.css`, `settings.html` from git (all additive/override edits).
- No migration, no schema change. No Tabler source or logo asset modified.

## Dependencies

- None external.
