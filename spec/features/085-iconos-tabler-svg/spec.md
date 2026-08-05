# 085 — Sustituir SVG inline por iconos Tabler (webfont `ti`)

## Objetivo
Eliminar todos los `<svg>` inline de iconos Tabler de las páginas web y reemplazarlos por iconos webfont Tabler (`<i class="ti ti-*">`). Esto unifica el estilo de iconos, reduce HTML (~163 SVG → 1 línea cada uno), elimina el `per-file-ignore` E501 de `utils_filters.py` y aprovecha el CSS `tabler-icons.min.css` ya cargado globalmente en `head.html`.

## Contexto
- La UI usa Tabler.io y ya carga `static/dist/css/tabler-icons.min.css` en `templates/includes/base/head.html`, incluido por `base.html` y `base-auth.html`. Toda página web (pública y dashboard) hereda de uno de esos layouts → el webfont está disponible en todas.
- El proyecto mezcla **iconos SVG inline** (bloques de ~400-900 chars) con **iconos webfont** `ti ti-*` (ya usados en parte de la UI). Esta feature unifica hacia webfont.
- Inventario verificado (sin contar emails):
  - **A · `utils_filters.py`**: 7 SVG en `get_icon_for_action` (`apps/core/templatetags/utils_filters.py:31-42`), usado en `profile.html:102` vía `|safe`. Causa del `per-file-ignore` E501.
  - **B · SVG con clase `icon-tabler-*`**: **163** en 54 archivos web (~42 nombres únicos; trash×31, edit×18, file-download×12, eye×11, file-type-pdf×7, brand-x/telegram/instagram/facebook×7 c/u, etc.). Sustitución 1:1: `<svg class="...icon-tabler-NOMBRE...">…</svg>` → `<i class="ti ti-NOMBRE">`.
  - **C · SVG Tabler sin clase nombrada**: ~25, identificables por su path `d` (no tienen `icon-tabler-*` en clase). Se mapean por path: navbar/sidebar (tema claro/oscuro), superuser_kpis (user, shield-check, world), pronosticos + empty_state (cloud-off), resumen_comercial (currency-dollar, circle-check), errores 400/403/404/500 (arrow-left), password/reset (mail), profile/update (trash), confirm_delete (alert-triangle), register (circle-check), invoice/create (edit), service/update (eye), payment/qr (13 iconos), pdf_avatar (file-type-pdf).
- **NO sustituibles** (quedan como SVG/PNG):
  - **Emails** (`*/emails/*`, ~20 SVG): los clientes de correo no cargan webfonts externas → los SVG inline son necesarios. NO tocar.
  - **Logo institucional** (`templates/includes/partials/logo.html` y en emails): gráfico de mapa, no es icono Tabler.
  - **QR de pago** (`payment/qr.html`): es `<img>` PNG en `static/dist/img/QR/QR.png` (el SVG con clase del archivo es el icono que SÍ se sustituye).
  - **Gráfico de arcos meteorológicos** (`apps/home/templates/pages/home/index.html`, transform rotate): gráfico, no icono.
  - **SVG en `<script>`/JS**: no son markup de página.
- Las plantillas de detalle/listado que renderizan `<i class="ti ti-*">` ya existen como referencia (Tabler por defecto).

## Criterios de aceptación
- [x] `get_icon_for_action` reescrito para devolver `<i class="ti ti-* text-*">` (sin `|safe` en `profile.html:102`): circle-plus→green, edit→orange, trash→red, login-2→green, logout→red, settings→currentColor, info-circle→gray.
- [x] Eliminado `"apps/core/templatetags/utils_filters.py" = ["E501"]` de `pyproject.toml`; `ruff check .` → 0 errores.
- [x] Los **163** SVG con clase `icon-tabler-*` en páginas web reemplazados por `<i class="ti ti-NOMBRE">` (1:1, conservando `text-*`/`text-secondary` del stroke o clase según contexto).
- [x] Los **~25** SVG sin clase mapeados por path `d` → `ti-*` correctos.
- [x] Ningún `<svg>` Tabler queda en páginas web (solo los NO sustituibles: emails, logo, QR PNG, arcos, JS).
- [x] Todos los nombres `ti-*` usados existen en `static/dist/css/tabler-icons.min.css` (verificación automatizada con grep del CSS).
- [x] No se tocó ningún template de `*/emails/*`.
- [ ] Verificación: `manage.py check` OK, suite completa OK, `djlint . --reformat --check` + `--lint` → 0 (pendiente render visual)
- [ ] Roadmap: 085 → Hecho. Commit descriptivo (sin push, lo sube el usuario).

## No objetivos
- No sustituir SVG de templates de email (webfont no funciona en correo).
- No tocar logo institucional, QR PNG, gráficos meteorológicos ni SVG dentro de JS.
- No cambiar colores/estilos visuales de los iconos (solo el mecanismo de render).
- No cambiar estructura HTML de layouts ni incluir nuevos assets.

## Notas
- El webfont Tabler usa clases `ti ti-<nombre>`; el tamaño se controla con la clase `icon` o por tamaño de fuente. En los casos actuales con `width/height` o `class="icon"`, mantener `class="icon ti ti-*"`.
- La clase `icons-tabler-outline` (en SVG) no tiene equivalente en webfont; se ignora.
- Los iconos sin color explícito heredan `currentColor`; los que hoy usan `stroke="green|orange|red|gray"` se sustituyen por `text-green|text-orange|text-red|text-secondary` sobre el `<i>`.
