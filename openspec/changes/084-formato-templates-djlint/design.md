# 084 — plan

## Objetivo
Unificar formato de templates con djlint (indentación 2 espacios, profile django), integrado a pre-commit y CI. Los emails whitespace-sensitive se excluyen del formateo.

## Decisiones previas
- **Herramienta**: djlint (estándar de facto). Revierte la decisión "sin djlint" de 083.
- **Indentación**: 2 espacios (patrón `customer/create.html` y layouts).
- **Emails**: excluidos del reformat (`ignore = ["**/emails/**"]`) — el HTML de correo es whitespace-sensitive. Solo se les añade newline final.
- **Profile**: `django` (no aplica reglas Jinja/Nunjucks/Handlebars).
- **Integración**: pre-commit **y** CI (job `templates` en ci.yml).
- **Diff grande**: ~161 templates tocados una sola vez (aceptado, como con Ruff en 083).
- **Revisión previa a aplicar**: dry-run `--reformat --check` + inspección manual de diff en templates representativos.

## Fases (secuenciadas)
1. **Fase A — Base limpia**: commit de 083 (hecho, `67ebe99`).
2. **Fase B — Spec/plan/tasks** (este doc).
3. **Fase C — Instalación**: `djlint==1.44.0` en `requirements-dev.txt` + instalar en venv.
4. **Fase D — Config**: `[tool.djlint]` en `pyproject.toml`.
5. **Fase E — Dry-run + revisión**: `djlint . --reformat --check`; inspeccionar diff de un CRUD, un list y un include.
6. **Fase F — Aplicar**: `djlint . --reformat`.
7. **Fase G — Lint**: `djlint . --lint` hasta 0 errores (ignores justificados).
8. **Fase H — Emails**: newline final sin reindentar.
9. **Fase I — Integración**: pre-commit hook + CI job.
10. **Fase J — Docs**: AGENTS.md.
11. **Fase K — Verificación**: check + suite + render visual.
12. **Fase L — Cierre**: roadmap 084 → Hecho, commit descriptivo (sin push).

## Riesgos
- **djlint altera HTML renderizado**: los `{% if %}` dentro de atributos pueden introducir espacios → mitigado con `format_attribute_template_tags` evaluado en dry-run y revisión de diff.
- **Emails whitespace-sensitive**: mitigado excluyéndolos del formateo.
- **Reglas de lint ruidosas** (H005/H030 metadatos, T001/T003 nombres de block): se ignoran con justificación en spec.
- **Diff enorme y mezcla con 083**: mitigado commitando 083 primero.

## Verificación
- `djlint . --reformat --check` → sin diferencias tras aplicar.
- `djlint . --lint` → 0 errores.
- `python manage.py check` → OK.
- `python manage.py test` → 283 OK.
- Render visual: home, login, un CRUD (create/update), dashboard.
