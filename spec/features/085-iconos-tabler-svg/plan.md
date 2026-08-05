# 085 — plan

## Enfoque
Sustitución mecánica asistida por regex, verificada nombre a nombre contra el CSS webfont local (`tabler-icons.min.css`). Se procesa por capas para evitar errores:

1. **A · templatetag** — reescribir `get_icon_for_action` a mano (solo 7 iconos) y quitar `|safe` del template. Eliminar el ignore E501.
2. **B · SVG con clase** — transformación regex 1:1 en 54 archivos: `icon-tabler-NOMBRE` → `ti ti-NOMBRE`, eliminando el bloque `<svg>…</svg>`. Conservar clases de color.
3. **C · SVG sin clase** — mapear por path `d` con reemplazo manual por archivo (los paths Tabler son únicos).
4. **Verificación** — extraer todos los `ti ti-*` del repo y comprobar contra el CSS local; render visual de páginas clave.

## Riesgos y mitigaciones
| Riesgo | Mitigación |
|---|---|
| Nombre `ti-*` no existe en webfont | Verificación automatizada contra `tabler-icons.min.css` (grep de cada clase) |
| SVG con clase 1:1 que no es icono Tabler | Solo se tocan los que contienen `icon-tabler-`; el resto no se toca |
| Cambiar look por perder `stroke` de color | Mapear `stroke="color"` → `text-color` en la misma transformación |
| Romper render de emails | Excluir `*/emails/*` de TODOS los reemplazos |
| `|safe` necesario para webfont | NO: `<i>` no necesita `|safe`; quitarlo (mejora seguridad) |

## Orden de implementación
1. Fase A: templatetag + template + pyproject (independiente, desbloquea E501).
2. Fase B: sustitución 1:1 de los 163 (mecánica, por grupos de archivos).
3. Fase C: mapeo por path de los ~25 (manual, por archivo).
4. Fase E: verificación CSS + lint + tests + render.
5. Fase F: docs + roadmap + commit.

## Verificación
- `grep` de clases `ti ti-*` vs CSS local → todos presentes.
- `ruff check .` (0 errores, sin E501 en utils_filters).
- `djlint . --reformat --check` + `djlint . --lint` → 0.
- `python manage.py check` + `python manage.py test` (suite completa).
- Render: profile timeline, dashboard KPIs, payment QR, error pages (400/403/404/500), empty_state, pdf_avatar, register, confirm_delete.
