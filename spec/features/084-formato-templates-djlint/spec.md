# 084 — Formato de templates con djlint

## Objetivo
Unificar la indentación, formato y estilo de los 166 templates del proyecto (en `templates/` y `apps/*/templates/`) usando djlint como formateador y linter, con indentación de **2 espacios** y `profile = "django"`. Integrar djlint a pre-commit y CI para que la consistencia se mantenga en el tiempo.

## Contexto
- El 84% de los templates (140/166) no sigue la indentación de 2 espacios del patrón de referencia `apps/commercial/.../customer/create.html`.
- Problemas detectados: trailing whitespace (~100+ líneas), 27 archivos sin newline final, 1 con tabs (`templates/includes/base/scripts.html`), atributos multi-línea con alineaciones inconsistentes, `{% %}` indentados a niveles arbitrarios.
- No hay tags custom en templates propios (solo estándar Django) → djlint funciona sin configuración especial.
- **5 templates de email whitespace-sensitive** (`emails/`): certificate, invoice, invoice_qr, notification, password_reset_email. El HTML inline de correo depende del whitespace para renderizar bien en clientes → **se excluyen del formateo**.
- djlint no está instalado. La feature 083 lo descartó; esta feature lo adopta.

## Criterios de aceptación
- [x] `djlint==1.44.0` en `requirements-dev.txt` e instalado en el venv.
- [x] Config `[tool.djlint]` en `pyproject.toml`: `profile = "django"`, `indent = 2`, `extend_exclude` de carpetas no-template (`emails`, `static`, `media`, `logs`, `migrations`, `spec`). Reglas `ignore` justificadas: `H005`, `H016`, `H021`, `H023`, `H026`, `H030`, `H037`, `D018`.
- [x] `djlint . --reformat` aplicado: 141 templates reindentados a 2 espacios.
- [x] `djlint . --lint` → 0 errores. Corregido además: 2 links `http://` → `https://` en `templates/includes/home/footer.html` (H022).
- [x] Templates de email excluidos del formateo; solo se les añadió newline final (certificate, invoice, invoice_qr).
- [x] Hook djlint en `.pre-commit-config.yaml` (`djlint-lint` + `djlint-reformat`, rev v1.44.0).
- [x] Job `templates` en `.github/workflows/ci.yml` con `djlint --reformat --check` y `djlint --lint`.
- [x] `AGENTS.md` actualizado con la convención (2 espacios, djlint, emails excluidos).
- [x] Verificación: `manage.py check` OK, suite completa 283 OK, 161 templates compilan sin errores, render de páginas públicas y CRUDs con formset 200.
- [x] Roadmap: 084 → Hecho. Commit descriptivo (sin push, lo sube el usuario).

## No objetivos
- No tocar templates del admin de Django ni de librerías (`.venv`).
- No reindentar los templates de email.
- No cambiar estructura HTML ni comportamiento de las páginas.

## Reglas de lint ignoradas (con justificación)
- **H021** (inline styles): Tabler usa estilos inline extensivamente (SVGs, colores de iconos).
- **H023** (entity references): `&laquo;`, `&copy;`, `&raquo;` son válidas y legibles.
- **H030** (meta description): los layouts no son páginas de aterrizaje SEO.
- **H016** / **H005** (lang/title en `<html>`): los layouts ya tienen `lang="es"`; falsos positivos en includes.
- **H026** (empty id/class): tablas genéricas rellenadas en runtime por JS/DataTables.
- **H037** (duplicate attribute): falso positivo verificado (no hay `class` duplicado real tras el reformat).
- **D018** (links internos con `{% url %}`): los `href` con `data-fslightbox` apuntan a imágenes de satélite, no a URLs de Django.

## Notas
- El CLI de djlint 1.44 usa `indent` (no `indentation`) como clave de configuración; `extend_exclude` recibe regex sobre la ruta relativa (no globs).
- Los ignores del lint no se aplican al reformat (el formato sigue siendo completo sobre los templates no excluidos).
