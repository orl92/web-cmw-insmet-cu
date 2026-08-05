# 083 — Automatización de dependencias y CI/CD

**Estado:** en desarrollo

## Qué hace

Sustituye el workflow de CodeQL (imposible de ejecutar en repo privado con cuenta personal Free, requiere GitHub Advanced Security de pago) por un pipeline CI/CD completo y gratuito, y automatiza la actualización de dependencias con Dependabot + auto-merge de updates menores/patch.

## Por qué

1. **CodeQL falla continuamente**: el repo es privado en cuenta personal Free; `github/codeql-action/init` falla en cada push porque el escaneo de código en repos privados requiere GitHub Advanced Security (solo disponible en planes Team/Enterprise). No es un error de configuración, es una limitación de licencia. El check rojo ensucia el historial de commits.
2. **Dependencias desactualizadas**: no hay Dependabot configurado, el usuario debe revisar alertas manualmente (de hecho detectó la actualización de Django 5.2.15 por dependabot remoto).
3. **Sin quality gates**: no hay CI que corra tests, lint ni escaneo de seguridad en cada push/PR. Los 283 tests solo se ejecutan localmente.
4. **Sin lint configurado**: no hay `pyproject.toml`, Ruff ni pre-commit.

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
- [x] Dependencias con vulnerabilidades actualizadas: Django 5.2.16, cryptography 50.0.0, pillow 12.3.0, pypdf 6.14.2.
- [x] Roadmap actualizado: 083 → Hecho; nota de configuración manual en GitHub Settings (branch protection, auto-merge de Dependabot).

## Notas de seguridad (bandit y pip-audit)

- **`verify=False`** en 3 llamadas a la API interna `apimet.cmw.insmet.cu` (transporte HTTP interno ya no-cifrado): anotadas `# nosec B501` en `apps/home/views/modelos/views.py`.
- **`mark_safe`** en `apps/core/templatetags/utils_filters.py` es el sanitizador XSS (escapa todo y solo permite allowlist de tags/atributos): anotado `# nosec B703`.
- **pdfkit 1.0.0** (PYSEC-2026-2860): command injection vía URLs no confiables; el proyecto usa `pdfkit.from_string` con HTML interno → ignorado en CI con `--ignore-vuln` y sin fix disponible.
- **Bandit** corre con `-ll` (severidad media+) y excluye tests y migraciones.

## Fuera de alcance

- Branch protection en `main` (requerir status checks/review) — se configura en GitHub Settings, no se versiona. Solo se documenta en el spec.
- Activar "auto-merge" de Dependabot en GitHub UI — acción manual del usuario.
- Despliegue automático a producción (deploy sigue siendo manual vía Supervisor).
- Docker Compose, health check endpoint, backup automatizado (backlog separado).
- djlint para templates Django.

## Decisión técnica: por qué bandit separado de ci.yml

`pip-audit` ya cubre vulnerabilidades de dependencias. `bandit` es SAST estático de código Python (XSS, SQLi, `eval()`, etc.) — complementa, no solapa. Va en workflow separado para no bloquear el merge en CI por hallazgos de bajo nivel que requieren juicio humano; se configura para fallar solo en severidad media+ realista.

`pip-audit` corre con `-r requirements.txt` (audita el árbol del proyecto, sin ruido de la vulnerabilidad del propio pip del runner). Los hallazgos con fix se actualizan directamente; los sin fix se ignoran explícitamente con `--ignore-vuln` y se documentan aquí.
