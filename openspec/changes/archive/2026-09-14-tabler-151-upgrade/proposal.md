# Proposal: Tabler upgrade to 1.5.1

## Intent

The portal vendors Tabler core **1.4.0** (`static/dist/css|js`) + Icons webfont **3.45.0**. The upcoming `landing-page` change needs the `social-gray` style (`social-app-*`, `tabler-socials.min.css`, `img/social/`), which only ships with core 1.5.1. Upgrade the vendored assets now, fix the 1.5 color-mode default (`auto` → OS dark would take over), and prove the 020 theme contract survives.

## Scope

### In Scope
- **Vendor swap** — core css/js 1.4.0 → 1.5.1; icons webfont 3.45.0 → **3.46.0**; add `tabler-socials.min.css` + `img/social/`.
- **Re-patch `tabler-theme.min.js`** on the 1.5.1 base (existing project patch): toggle light/dark only; never touch `data-bs-theme-base/-font/-primary/-radius`.
- **Color-mode fix** in `head.html` — set `data-bs-theme="light"` explicitly when not dark (official 1.5 guidance) instead of removing the attr.
- **`maps.js` fix** — `window.bootstrap` is gone in 1.5.1 (UMD exposes `tabler`); `bootstrap.Toast` → `(window.tabler && window.tabler.bootstrap) || window.bootstrap` pattern already used in `utils.js`/`document-modal.js`. Additionally, replace the toast's FontAwesome icons (`fas fa-*`) with the Tabler webfont (`ti ti-*`) already vendored in the project.
- **Verify 020 contract** — model `theme_base` (slate/gray/zinc/neutral/stone) presets still resolve in 1.5.1 `tabler-themes.min.css`; patched loader must not wipe model-seeded attrs.
- **No-regression gate** — `manage.py check`, affected app tests, djlint, visual smoke (public + dashboard, light + dark).

### Out of Scope
- 020 rework (active, first in sequence) and `landing-page` (socials usage, URLs, footers).
- Unrelated libs (apexcharts, datatables…) — vendored apart from Tabler; no npm/build.

## Capabilities

### New Capabilities
- `tabler-core-vendor`: versioned, vendored Tabler assets (core 1.5.1, icons 3.46.0, socials), no build step, CDN never referenced in templates.

### Modified Capabilities
- `tema-personalizado` (007): explicit server-side light default; patched theme loader re-derived on 1.5.1; `data-bs-theme-base` semantics verified.

## Approach

Swap min builds from `@tabler/core@1.5.1` + `@tabler/icons-webfont@3.46.0` (official CDN = inventory reference only). Re-apply the project patch to 1.5.1 `tabler-theme.min.js`, keeping the provenance header. Adjust `head.html` inline theme script (explicit light), fix `maps.js`, then run the no-regression gate.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `static/dist/css/tabler.min.css`, `tabler-themes.min.css` | Modified | 1.4.0 → core 1.5.1 |
| `static/dist/js/tabler.min.js` | Modified | 1.4.0 → core 1.5.1 |
| `static/dist/js/tabler-theme.min.js` | Modified | patch re-applied on 1.5.1 |
| `static/dist/css/tabler-icons.min.css` + `fonts/tabler-icons.*` | Modified | webfont 3.45.0 → 3.46.0 |
| `static/dist/css/tabler-socials.min.css` + `img/social/` | New | ships with 1.5.1 (34 SVGs incl. `*-gray`) |
| `templates/includes/base/head.html` | Modified | explicit `data-bs-theme="light"` when not dark |
| `static/dist/js/maps.js` | Modified | `bootstrap.Toast` → fallback pattern |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| `window.bootstrap` removal breaks `maps.js` | High | fix in scope; fallback already standard |
| Visual drift (system fonts, softer shadows, dark link tint) | Med | smoke test; accept unless brand-breaking |
| 1.5.1 themes CSS missing a model preset | Low | verify the 5 selectors; align via 020 follow-up |
| Browser floor raised (Chrome 123/FF 128/Safari 17.5) | Low | document; internal intranet users |

## Rollback Plan

`git revert` the vendored swaps + `head.html`/`maps.js` edits, re-run `collectstatic`. No schema or migration.

## Dependencies

- `@tabler/core@1.5.1`, `@tabler/icons-webfont@3.46.0` (one-time download, then vendored).
- 020 merged first (approved sequence).

## Success Criteria

- [ ] Vendored 1.5.1 + icons 3.46.0 + socials present; zero CDN links; no npm/build.
- [ ] `tabler-theme.min.js` header records the re-applied patch; only theme toggle managed.
- [ ] OS-dark visitor with no stored choice sees LIGHT; `?theme=dark` and navbar toggle still work.
- [ ] Model `theme_base` renders on `<html>` and looks identical pre/post upgrade.
- [ ] Maps page toast fires (no ReferenceError).
- [ ] Smoke test + `manage.py check` + app tests + `djlint --reformat --check` pass.
