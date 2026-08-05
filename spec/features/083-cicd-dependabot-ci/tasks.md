# 083 — tasks

## Fase A — Workflows GitHub Actions

- [x] **T1** Eliminar `.github/workflows/codeql.yml`.
- [x] **T2** Crear `.github/workflows/ci.yml`: jobs paralelos con cache de pip —
  - `test`: setup-python 3.12 + `pip install -r requirements.txt` + `python manage.py test`.
  - `lint`: `pip install -r requirements-dev.txt` + `ruff check .`.
  - `security`: `pip install -r requirements-dev.txt` + `pip-audit` + `python manage.py makemigrations --check --dry-run`.
  - Triggers: `pull_request` y `push` a `main`; `concurrency` cancelando runs previos; `permissions: contents: read`.
- [x] **T3** Crear `.github/dependabot.yml`: ecosistemas `pip` y `github-actions`, `directory: /`, `schedule.interval: weekly`, `open-pull-requests-limit: 5`, grupos `pip-minor-patch` y `github-actions`.
- [x] **T4** Crear `.github/workflows/dependabot-auto-merge.yml`: `dependabot/fetch-metadata` + `actions/github-script` — aprueba y mergea PRs de dependabot cuando `update_type` es `version-update:semver-minor` o `semver-patch` y CI pasa; majors se dejan manuales.
- [x] **T5** Crear `.github/workflows/security.yml`: bandit sobre `apps/ config/ manage.py` con umbral severidad media+ y excludes de tests/migrations; no bloquea merge (continue-on-error false pero con config razonable).

## Fase B — Tooling local

- [x] **T6** Crear `pyproject.toml`: sección `[tool.ruff]` — `target-version = "py312"`, `line-length = 100`, `exclude = [".venv", "staticfiles", "static", "*/migrations/*", "schema.yml"]`; `[tool.ruff.lint]` selección por defecto + `per-file-ignores` justificados. Añadir `[tool.bandit]` excludes.
- [x] **T7** Crear `requirements-dev.txt`: `ruff`, `bandit`, `pip-audit` (versiones fijas); `requirements.txt` se deja intacto (solo runtime).

## Fase C — Lint del repo

- [x] **T8** Instalar dev deps en venv: `pip install -r requirements-dev.txt`.
- [x] **T9** `ruff check . --fix` → corregir automático (imports, formato).
- [x] **T10** `ruff check .` → corregir a mano restantes hasta 0 errores (con `# noqa` solo donde justificado).
- [x] **T11** Verificar: `python manage.py check` + `python manage.py test` (283 OK).

## Fase D — Pre-commit y SECURITY

- [x] **T12** Crear `.pre-commit-config.yaml`: `ruff` (lint + format), `check-merge-conflict`, `end-of-file-fixer`, `detect-secrets`. Sin djlint.
- [x] **T13** Reescribir `SECURITY.md`: versión soportada (Django 5.2 / proyecto), cómo reportar vulnerabilidad (email institucional + issue privado), política de divulgación.

## Verificación y cierre

- [x] **T14** `python manage.py check` y suite completa OK (283 tests). Revisión del diff: ruff no debe haber cambiado lógica, solo estilo.
- [x] **T15** Actualizar `spec/constitution/roadmap.md`: 083 → Hecho; nota "Branch protection y auto-merge de Dependabot se activan en GitHub Settings (no versionable)".
- [x] **T16** Commit descriptivo (083). El push lo hace el usuario en VS Code.
