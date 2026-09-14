# Tasks: Tabler core 1.4.0 → 1.5.1 vendor swap + theme/maps fixes

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ≈120 authored + ~4.2 MB vendored goldens (excl.) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

> `Decision needed = No`: forecast es LOW y el único decision point (chain split) no se activa. Con `ask-on-risk`: si en apply la diff autored cruza las 400 líneas, el orquestador frena y pregunta.

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Swap 1.5.1 + 4 fixes + gate | PR 1 | `manage.py check` && `manage.py test apps.core apps.meteo apps.home` | `runserver` + smoke light/dark (maps toast, datatables, Tempus, modales) | `git revert` swap + edits + `collectstatic --no-input` (sin schema) |

## Phase 1: Vendor Swap (assets)

- [x] 1.1 Bajar tarballs `@tabler/core@1.5.1` + `@tabler/icons-webfont@3.46.0` a `/tmp/opencode/t151` y extraer; verificar tamaños contra design (`wc -c`)
- [x] 1.2 Reemplazar `static/dist/css/tabler.min.css` + `tabler-themes.min.css` + `static/dist/js/tabler.min.js` (core 1.5.1)
- [x] 1.3 Reemplazar `static/dist/css/tabler-icons.min.css` + `static/dist/fonts/tabler-icons.{woff2,woff,ttf}` (3.46.0); rebase `./fonts/` → `../fonts/` en el css
- [x] 1.4 Copiar `tabler-socials.min.css` → `static/dist/css/` y `img/social/` (50 SVGs) del paquete 1.5.1
- [x] 1.5 Verificación estática: headers de procedencia (v1.5.1/3.46.0) en los 4 assets, `grep -o 'data-bs-theme-base=[a-z]*'` → 5 presets, cero residuos 1.4.0/3.45.0, `node --check tabler-theme.min.js`

## Phase 2: Theme + Loader (delta 007)

- [x] 2.1 RED: crear `apps/core/tests/test_tabler_upgrade.py` — home/dashboard renderizan `<html data-bs-theme="light">`; head.html contiene pre-paint `setAttribute` + `?v=151` en los 4 assets; cero `cdn.jsdelivr.net`/`unpkg.com` en templates + `static/dist/`; maps.js usa fallback `(window.tabler && window.tabler.bootstrap) || window.bootstrap` e iconos `ti ti-*` sin `new bootstrap.Toast(`/`fas `
- [x] 2.2 Re-parchear `static/dist/js/tabler-theme.min.js` sobre base 1.5.1: solo toggle light/dark (única key `tabler-theme`), default `light`, `setAttribute` siempre, header de procedencia (design §Interfaces)
- [x] 2.3 `templates/layouts/base.html` + `base-auth.html`: `<html lang="es" data-bs-theme="light">` + comentario header a 1.5.1 — verifica 2.1
- [x] 2.4 `templates/includes/base/head.html`: script inline pre-paint (`?theme` → `localStorage["tabler-theme"]` → `setAttribute`), sin tocar base/font/primary/radius; `?v=151` en los links swapped

## Phase 3: Maps Toast (UMD + iconos)

- [x] 3.1 `static/dist/js/maps.js` `showToast()`: helper fallback Bootstrap; iconos `ti ti-circle-check`/`ti ti-alert-triangle`/`ti ti-info-circle` reemplazando `fas fa-*` (línea 300); conservar remoción en `hidden.bs.toast` — verifica 2.1

## Phase 4: Gate + Smoke + Commit

- [x] 4.1 Gate completo: `python manage.py check`; `python manage.py test apps.core apps.meteo apps.home` (442 OK); `djlint --reformat --check` sobre templates tocados (0 pendientes); `python manage.py collectstatic --no-input` (460 archivos)
- [x] 4.2 Smoke (harness HTTP, test client + DB desechable, 54/54): `/` y `/dashboard/` renderizan LIGHT explicit (no auto); maps (`home:models_maps`) incluye maps.js + `toast-container` + sin `fas ` inline; `meteo:pronostico_list` (datatables) y `meteo:pronostico_create` (Tempus assets + `data-tempus`) OK; `theme=dark` 200 (attr light server-side, dark cliente-side); 5 presets `theme_base` fluyen al JSON del modelo; estáticos resuelven (incl. socials + fuentes) con proveniencia 1.5.1/3.46.0 — verificación navegador completada en 4.6 con medición headless (toast/modal/paleta no interactivos: no aplican al core del upgrade; el resto es cover de 1.5.1/3.46.0)
- [x] 4.3 Commits separados (goldens vendored vs. edits autorales), conventional commits, revisión con subagente antes de commit (AGENTS.md), sin co-author
- [x] 4.4 RED: test de regresión — dashboard renderiza `<html lang="es" data-bs-theme="light" data-bs-navbar-position="vertical">`; base.html declara el atributo (el core 1.5.1 oculta el sidebar cuando `.page` tiene navbar horizontal y no se declara posición; smoke 4.2 no lo detectó porque el test client no evalúa CSS)
- [x] 4.5 Fix: declarar `data-bs-navbar-position="vertical"` en `<html>` de `templates/layouts/base.html` — desactiva la exclusión (rule 1/1b) y restaura `--tblr-sidebar-width` (16rem); la navbar horizontal sigue visible porque `includes/dashboard/navbar.html` usa `d-lg-flex` (display:flex!important gana a la rule 2). Verificación: `manage.py test apps.core.tests.test_tabler_upgrade` + navegador (4.6: sidebar visible 256px en x=0, attr `vertical` confirmado con Playwright/Firefox headless)
- [x] 4.6 Fix iconos overflow: en 1.5.1 `.icon` es `display:inline-block` con box fija `width/height:var(--tblr-icon-size)` (default 1.25rem); un `font-size:` inline crecía el glifo fuera de la caja (iconos de KPI y comerciales saliéndose del card). Reemplazado por `style="--tblr-icon-size:NNpx"` (mismo tamaño, box + glifo escalan juntos) en 20 iconos de 8 templates: `dashboard/superuser_kpis.html` (4×48), `dashboard/resumen_comercial.html` (6×48), `dashboard/footer.html` (4×20), `partials/pdf_avatar.html` (36), `home/services/service_detail.html` (48), `home/models/maps.html` (48), `home/payment/qr.html` (32+3×20). RED→GREEN: `test_webfont_icons_scaled_via_icon_size_variable_not_font_size` (contrato global regex sobre templates/ + apps/) pasó de fallar a OK (14 tests); `check` y pre-commit (ruff/djlint/secrets) Passed; commit `1d0419c`. **Verificación navegador completada (4.2/4.5 WARNING resuelto)**: preview HTML real (render de `/dashboard/` y `/` con los views, estáticos reescritos a file://) medido con Playwright + Firefox headless 1600×1400: dashboard 35 iconos `.icon.ti` → 0 overflow vs. su card, sidebar vertical visible 256px en x=0, `data-bs-navbar-position="vertical"` presente; home 26 iconos → 0 overflow, attr ausente (portal horizontal, correcto). **Post-verify (WARNING sdd-verify cerrado)**: el mismo anti-patrón existía en iconos generados por JS propio — corregidos a `--tblr-icon-size` en `static/dist/js/maps.js` (3×24, toast), `static/dist/js/utils.js` (4×24, toast) y `static/dist/js/map_station.js` (3×44, leyenda de estaciones); el contrato se amplió para escanear también los `.js` no-min de `static/dist/js/` (y no solo `*.html` de templates/ + apps/) — 14/14 OK
