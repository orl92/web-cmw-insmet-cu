# 084 — tasks

## Fase A — Base limpia
- [x] **T1** Commit de 083 (`67ebe99`) — base limpia antes de tocar templates.

## Fase B — Spec/plan/tasks
- [x] **T2** Crear spec.md, plan.md, tasks.md de 084.

## Fase C — Instalación
- [x] **T3** Añadir `djlint==1.44.0` a `requirements-dev.txt` e instalar en el venv.
- [x] **T4** Verificar `djlint --version` en el venv.

## Fase D — Config
- [x] **T5** `[tool.djlint]` en `pyproject.toml`: `profile = "django"`, `indentation = 2`, `indent_type = "spaces"`, `format_attribute_template_tags = true` (evaluar en dry-run), ignores: `["**/emails/**", "static", "staticfiles", ".venv", "*/migrations/*", "spec"]`.
- [x] **T6** Documentar ignores de reglas de lint a medida que aparezcan (H/T codes).

## Fase E — Dry-run + revisión
- [x] **T7** `djlint . --reformat --check` → listar archivos que cambiarían.
- [x] **T8** Revisar diff en 3 templates representativos (CRUD, list, include) y confirmar resultado 2 espacios.

## Fase F — Aplicar reformat
- [x] **T9** `djlint . --reformat` → aplicar a todos los templates excepto emails.

## Fase G — Lint
- [x] **T10** `djlint . --lint` → resolver/ignorar reglas hasta 0 errores.
- [x] **T11** `djlint . --reformat --check` → sin diferencias.

## Fase H — Emails
- [x] **T12** Añadir newline final a los 5 emails sin reindentar (end-of-file).

## Fase I — Integración
- [x] **T13** Hook djlint en `.pre-commit-config.yaml` (lint + format check, profile django, mismos ignores).
- [x] **T14** Job `templates` en `.github/workflows/ci.yml` con `djlint --check`.

## Fase J — Docs
- [x] **T15** Actualizar `AGENTS.md`: convención templates (2 espacios, djlint, emails excluidos).

## Fase K — Verificación
- [x] **T16** `python manage.py check` → OK.
- [x] **T17** `python manage.py test` → 283 OK.
- [x] **T18** Render visual: home, login, CRUD create/update, dashboard.

## Fase L — Cierre
- [x] **T19** Actualizar spec.md: criterios `[x]` + ignores documentados.
- [x] **T20** Roadmap: 084 → Hecho.
- [x] **T21** Commit descriptivo (sin push, lo sube el usuario).
