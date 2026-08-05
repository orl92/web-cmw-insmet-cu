# 085 — tasks

## Fase A — Templatetag `utils_filters.py`
- [ ] **T1** Reescribir `get_icon_for_action` (`apps/core/templatetags/utils_filters.py:31-42`) devolviendo `<i class="ti ti-* text-*">` para los 7 flags (1 circle-plus/green, 2 edit/orange, 3 trash/red, 4 login-2/green, 5 logout/red, 6 settings/currentColor, default info-circle/gray).
  - Acceptance: función sin `<svg>`, con `mark_safe` si es necesario para `<i>`, líneas cortas (sin E501).
  - Verify: `ruff check apps/core/templatetags/utils_filters.py`
  - Files: `apps/core/templatetags/utils_filters.py`
- [ ] **T2** Quitar `|safe` en `apps/user_auth/templates/pages/user_auth/profile/profile.html:102`.
  - Verify: render de profile 200.
- [ ] **T3** Eliminar `"apps/core/templatetags/utils_filters.py" = ["E501"]` de `pyproject.toml`.
  - Verify: `ruff check .` → 0 errores.

## Fase B — 163 SVG con clase `icon-tabler-*`
- [ ] **T4** Extraer inventario exacto de archivos y nombres (`icon-tabler-*` → `ti ti-*`) en páginas web, excluyendo `*/emails/*`.
- [ ] **T5** Aplicar sustitución regex 1:1 en los 54 archivos: reemplazar el bloque `<svg … class="… icon-tabler-NOMBRE …">…</svg>` por `<i class="icon ti ti-NOMBRE [text-*]">`, mapeando el `stroke` de color a `text-*`.
  - Verify: `grep -r 'icon-tabler-' templates apps --include='*.html'` (sin emails) → 0; `grep -rl '<svg' …` solo queda en NO sustituibles.

## Fase C — ~25 SVG sin clase (mapeo por path)
- [ ] **T6** Mapear y sustituir por archivo:
  - navbar/sidebar → `ti-moon`/`ti-sun` (toggle tema)
  - superuser_kpis → `ti-user`, `ti-shield-check`, `ti-world`
  - pronosticos + empty_state → `ti-cloud-off`
  - resumen_comercial → `ti-currency-dollar`, `ti-circle-check`
  - errores 400/403/404/500 → `ti-arrow-left`
  - password/reset → `ti-mail`; profile/update → `ti-trash`; confirm_delete → `ti-alert-triangle`; register → `ti-circle-check`; invoice/create → `ti-edit`; service/update → `ti-eye`; payment/qr (13) → ti-shield-check/clock/heart/mail/phone-call/download/share; pdf_avatar → `ti-file-type-pdf`.
  - Verify: render de cada página 200.
  - Files: templates incluidos en `templates/includes/`, `templates/layouts/*error*.html`, `apps/*/templates/pages/*/`

## Fase D — Verificación de nombres CSS
- [ ] **T7** Extraer todos los `ti ti-<nombre>` del repo (web, sin emails) y verificar contra `static/dist/css/tabler-icons.min.css`.
  - Verify: 0 nombres faltantes.

## Fase E — Lint + tests + render
- [ ] **T8** `ruff check .` → 0; `djlint . --reformat --check` → 0; `djlint . --lint` → 0.
- [ ] **T9** `python manage.py check` + suite completa OK.
- [ ] **T10** Render visual: profile timeline, dashboard KPIs, payment QR, error pages, empty_state, pdf_avatar, register, confirm_delete.

## Fase F — Cierre
- [ ] **T11** Spec: criterios `[x]`. Roadmap: 085 → Hecho.
- [ ] **T12** Commit descriptivo (sin push, lo sube el usuario).
