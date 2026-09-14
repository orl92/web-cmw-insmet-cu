# Design: Tabler core 1.4.0 → 1.5.1 vendor swap + theme/maps fixes

## Technical Approach

One-shot vendor replacement from official npm tarballs (download-time source only; zero runtime CDN/npm), then three surgical edits: re-patch `tabler-theme.min.js` on the 1.5.1 base (theme-only, default `light`), make light explicit server-side + pre-paint, and fix the `maps.js` UMD fallback. Satisfies `tabler-core-vendor` (VENDORED-VERSION-PIN, NO-CDN-NO-BUILD, UMD-EXPOSURE-CONTRACT, SOCIALS-PLUGIN, NO-REGRESSION-GATE) and the 007 delta (LIGHT-DEFAULT-EXPLICIT, THEME-LOADER-151, THEME-BASE-020-VERIFIED).

## Architecture Decisions

| # | Option | Tradeoff | Decision |
|---|---|---|---|
| D1 | Download source: npm tarball (`registry.npmjs.org`) vs CDN file-by-file | Tarball = single SHA-stable artifact, atomic copy of 50 SVGs; CDN = many requests, no integrity | **Tarball** (primary); jsDelivr flat listing used only for expected sizes |
| D2 | Loader patch: strip 1.5.1's 10-key loop to theme-only vs keep loop | Official loop accepts `?theme-base=…` URL params → visitor localStorage overrides admin theme; its removeAttribute-when-default branch can still race `applyConfig()` | **Theme-only loop** (root cause of 020 was exactly this loader class) |
| D3 | Default theme | 1.5.1 default is `auto` (follows OS) | **`light`** (LIGHT-DEFAULT-EXPLICIT) |
| D4 | Attribute writes | Official removes attr when value == default; spec scenarios inspect `<html>` attr | **Always `setAttribute`** — `<html>` invariantly carries `data-bs-theme` ∈ {light, dark} |
| D5 | Server-side light | Inline script only vs static attr on `<html>` | **Both**: static `data-bs-theme="light"` on `<html>` in `base.html`+`base-auth.html` (no-JS default, testable) + pre-paint script upgrades to dark (no FOUC) |
| D6 | Cache busting | Content swaps under stable URLs; dev refs use `{% static '' %}` so WhiteNoise manifest never hashes them | **`?v=151`** on the 4 swapped assets in `head.html` (pattern already used: fslightbox `?1692870487`) |

## Data Flow

```
server: <html data-bs-theme="light"> (layouts)        ← static default
head.html inline (pre-paint): URL?theme → localStorage["tabler-theme"] → "light"
        setAttribute("data-bs-theme", <resolved>)     ← dark upgrades, no flash
tabler-theme.min.js (body top): same resolution, setAttribute, ONLY "theme" key
tabler.min.css: [data-bs-theme=dark] overrides :root light vars
admin attrs (base/font/primary/radius): seeded by head.html + scripts.html applyConfig()
        — loader never reads/writes them nor their tabler-* keys
```

## File Changes

| File | Action | Notes |
|---|---|---|
| `static/dist/css/tabler.min.css` | Replace | 1.5.1 (693,779 B) |
| `static/dist/css/tabler-themes.min.css` | Replace | 1.5.1 (4,965 B); 5 presets verified below |
| `static/dist/js/tabler.min.js` | Replace | 1.5.1 (85,439 B) — UMD exposes `window.tabler.bootstrap`, zero `window.bootstrap=` |
| `static/dist/js/tabler-theme.min.js` | Replace | 1.5.1 base (1,340 B) + project patch |
| `static/dist/css/tabler-icons.min.css` | Replace | 3.46.0 (211,022 B); rebase `./fonts/` → `../fonts/` |
| `static/dist/fonts/tabler-icons.{woff2,woff,ttf}` | Replace | 3.46.0 (462,200 / 794,532 / 2,834,800 B) |
| `static/dist/css/tabler-socials.min.css` | Add | 1.5.1 (4,424 B) |
| `static/dist/img/social/` | Add | 50 SVGs (25 brands × color + `-gray`) — corrects proposal's "34" |
| `templates/layouts/base.html` | Modify | `<html lang="es" data-bs-theme="light">`; bump header comment to 1.5.1 |
| `templates/layouts/base-auth.html` | Modify | same (covers 400/403/404/500/maintenance) |
| `templates/includes/base/head.html` | Modify | inline script: `setAttribute` always; `?v=151` on tabler css/js links |
| `static/dist/js/maps.js` | Modify | `bootstrap.Toast` → fallback (below) |
| `apps/core/tests/test_tabler_upgrade.py` | Add | light-default + theme-base contract tests |

No 1.4.0/3.45.0 residual filenames exist to delete (all Replace same-name).

## Interfaces / Contracts

**`<html>` attribute contract** (all layouts):

| Attribute | Managed by | Allowed values |
|---|---|---|
| `data-bs-theme` | head inline + patched loader | `light` (default) \| `dark` — always present, never `auto` |
| `data-bs-theme-base` | site_branding + applyConfig | `slate\|gray\|zinc\|neutral\|stone` (default `gray`) |
| `data-bs-theme-font` / `-radius` / `-primary` | site_branding + applyConfig | admin-only |
| localStorage | patched loader | only `tabler-theme` written (`?theme=`); never the 4 admin keys |

**Patched loader** (`tabler-theme.min.js`, full file):

```js
/*! Tabler v1.5.1 ... MIT — Project patch: the admin-only theme settings
 * (base, font, primary, radius) come from SiteConfiguration, applied by
 * base/head.html (pre-paint) and base/scripts.html (applyConfig). This loader
 * manages ONLY the visitor light/dark toggle and never reads/writes
 * data-bs-theme-base/-font/-primary/-radius nor their tabler-* keys. The
 * 1.5.1 'auto' default and matchMedia listener are removed: default is light.
 */
!function(){"use strict";var q=new URLSearchParams(window.location.search).get("theme");
var t=q||localStorage.getItem("tabler-theme")||"light";if(q){localStorage.setItem("tabler-theme",t);}
document.documentElement.setAttribute("data-bs-theme",t);}();
```

**maps.js fix** — helper signature: `const Bootstrap = (window.tabler && window.tabler.bootstrap) || window.bootstrap;` living at the top of `showToast()` (mirrors `utils.js:2`; `document-modal.js:32` uses `var Bs`), then `new Bootstrap.Toast(toastElement)`. Keep the `hidden.bs.toast` removal. **Icon swap (user-approved)**: replace FontAwesome icon markup (`<i class="fas fa-*">`) inside the toast template with the Tabler webfont (`<i class="ti ti-*">`) — the webfont is already vendored, so no new asset lands.

## Download & Replacement Procedure

```bash
curl -sL -o /tmp/opencode/tabler-core-1.5.1.tgz https://registry.npmjs.org/@tabler/core/-/core-1.5.1.tgz
curl -sL -o /tmp/opencode/icons-webfont-3.46.0.tgz https://registry.npmjs.org/@tabler/icons-webfont/-/icons-webfont-3.46.0.tgz
mkdir -p /tmp/opencode/t151 && tar -xzf /tmp/opencode/tabler-core-1.5.1.tgz -C /tmp/opencode/t151
# swap: cp package/dist/{css/tabler.min.css,css/tabler-themes.min.css,css/tabler-socials.min.css} → static/dist/css/
#       cp package/dist/js/tabler.min.js → static/dist/js/
#       cp package/dist/js/tabler-theme.min.js → static/dist/js/tabler-theme.min.js  ← then apply the patch above
#       cp -r package/dist/img/social → static/dist/img/social
# icons: cp package/dist/tabler-icons.min.css → static/dist/css/ ; sed 's|\./fonts/|../fonts/|g'
#       cp package/dist/fonts/tabler-icons.{woff2,woff,ttf} → static/dist/fonts/
# integrity: wc -c against sizes above; grep header "v1.5.1"/"3.46.0"; node --check tabler-theme.min.js
```

## Testing Strategy

| Layer | What | How |
|---|---|---|
| Static | 5 theme-base selectors in 1.5.1 themes CSS | `grep -o 'data-bs-theme-base=[a-z]*' static/dist/css/tabler-themes.min.css` → slate/gray/zinc/neutral/stone ✓ (verified now: all 5 + `pink` alias + legacy `[data-theme-base=…]`; gray hexes identical to 1.4.0) |
| Static | gray palette drift | `git show HEAD:static/dist/css/tabler-themes.min.css` vs new: diff `--tblr-gray-*` blocks per preset |
| Django | `test_tabler_upgrade.py`: home & dashboard render `<html … data-bs-theme="light">`; head contains pre-paint setAttribute + `?v=151` links; templates carry zero `cdn.jsdelivr.net`/`unpkg.com` | `python manage.py test apps.core` |
| Gate | `python manage.py check`; `python manage.py test apps.core apps.meteo apps.home`; `djlint --reformat --check` on touched templates; `python manage.py collectstatic --no-input` | exact commands |
| Smoke | OS-dark → home `/` and `/dashboard/` render LIGHT; navbar `?theme=dark`/`?theme=light` toggle + reload persists; maps page (`home:models_maps`) toast fires with no ReferenceError and auto-hides; datatables page (meteo:pronostico_list) loads; Tempus picker opens on meteo:pronostico_create; delete/document modal opens/closes; admin sets each of 5 `theme_base` → palette identical pre/post | manual, light + dark, console clean |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary. The apply-time `curl`/`tar` are developer tooling, never runtime integration.

## Migration / Rollout

No DB/schema migration. Rollback: `git revert` the swap + 3 edits, re-run `collectstatic`. Prod cache handled by `?v=151`.

## Task Split (for sdd-tasks)

T1 download+integrity+inventory; T2 swap core css/js+headers; T3 icons swap+rebase; T4 socials copy; T5 re-patch loader + layouts attr + head.html (`?v=151`); T6 maps.js fallback; T7 `test_tabler_upgrade.py` + full gate; T8 visual smoke + commit. Review budget: LOW — vendored min assets are generated goldens (excluded); authored ≈ 120 lines.

## Open Questions

None blocking. Note: `?v=151` (D6) slightly widens head.html scope — justified, flag it in apply.
