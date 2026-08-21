# Spec — 083-cicd-dependabot-ci

## Criterios de aceptación

- [x] `.github/workflows/codeql.yml` eliminado.
- [x] `.github/workflows/ci.yml` creado con jobs paralelos:
  - **test**: Python 3.12, `pip install -r requirements.txt`, `python manage.py test` (283 tests).
  - **lint**: Ruff (`ruff check .`) sobre todo el repo, 0 errores.
  - **security**: `pip-audit -r requirements.txt` + `python manage.py makemigrations --check --dry-run`.
  - Cache de pip.
- [x] `.github/workflows/security.yml` con **bandit** (SAST estático Python) con umbral severidad media+.
- [x] `.github/dependabot.yml` con ecosistemas `pip` y `github-actions`, schedule semanal, `open-pull-requests-limit: 5`, grupos para menores/patch de pip.
- [x] `.github/workflows/dependabot-auto-merge.yml`: aprueba + mergea automáticamente updates de dependencia **no-major** cuando CI pasa; majors quedan para revisión manual.
- [x] `pyproject.toml` con config de Ruff (line-length, target py312, excludes de staticfiles, per-file-ignores justificados).
- [x] `requirements-dev.txt` con `ruff`, `bandit`, `pip-audit`; `requirements.txt` solo deps de runtime.
- [x] Ruff corriendo en TODO el repo: 0 errores. Per-file-ignores solo en: decodificadores WMO (`apps/api/data/*`), notación meteorológica (`plot_generators.py` N806), SVG inline (`utils_filters.py` E501).
- [x] `.pre-commit-config.yaml` con Ruff + `check-merge-conflict` + `end-of-file-fixer` + `detect-secrets`. Sin djlint.
- [x] `SECURITY.md` real (no template por defecto): versión soportada, cómo reportar vulnerabilidad.
- [x] Suite completa (283 tests) sigue OK tras el lint.
- [x] Dependencias con vulnerabilidades actualizadas: cryptography 50.0.0, pillow 12.3.0, pypdf 6.14.2.
- [ ] **Django 5.2.16 NO aplicado** — `requirements.txt` sigue en `Django==5.1.4`. Verificar si se revirtió y decidir en 093-deps-docs-alineacion (subir a 5.2.x o fijar 5.1.4 como versión soportada y corregir AGENTS.md/SECURITY.md).
- [x] Roadmap actualizado: 083 → Hecho; nota de configuración manual en GitHub Settings (branch protection, auto-merge de Dependabot).
