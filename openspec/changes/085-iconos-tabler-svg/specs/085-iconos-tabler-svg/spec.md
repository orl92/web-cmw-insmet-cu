# Spec — 085-iconos-tabler-svg

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
