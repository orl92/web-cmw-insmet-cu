# 083 — plan

## Objetivo
Reemplazar CodeQL (inviable en repo privado Free) por CI/CD gratuito y completo (test + lint + security scan) y automatizar dependencias con Dependabot + auto-merge no-major. Aplicar buenas prácticas de repo: pyproject/Ruff, requirements-dev, pre-commit, SECURITY.md real.

## Decisiones previas
- CodeQL se ELIMINA (no se puede hacer funcionar sin GitHub Advanced Security de pago).
- CI usa SQLite (tests ya corren con `IsolatedMediaRunner`); no se montan servicios Postgres.
- Python 3.12 (match con venv local).
- Ruff limpia TODO el código existente hasta 0 errores; excludes solo para lo justificable (venv/staticfiles/migrations).
- `pip-audit` en ci.yml (dependencias); `bandit` en workflow separado (SAST, no bloquea merge salvo severidad media+ realista).
- Auto-merge solo updates no-major de pip y github-actions; majors manuales.
- Sin djlint (decisión del usuario).
- Branch protection NO se versiona — se documenta en spec + SECURITY.

## Fases (secuenciadas)
1. **Fase A — Spec/plan/tasks** (este doc): estructura SDD completa.
2. **Fase B — Workflows**: eliminar `codeql.yml`; crear `ci.yml` (test+lint+security), `dependabot.yml`, `dependabot-auto-merge.yml`, `security.yml` (bandit).
3. **Fase C — Tooling local**: `pyproject.toml` (Ruff), `requirements-dev.txt` (ruff, bandit, pip-audit), `.pre-commit-config.yaml`.
4. **Fase D — Lint del repo**: instalar ruff, `ruff check . --fix`, corregir a mano lo restante hasta 0 errores; verificar suite completa (283 tests).
5. **Fase E — SECURITY.md real**: versión soportada + cómo reportar.
6. **Fase F — Cierre**: `manage.py check`, suite completa, roadmap 083 → Hecho, commit descriptivo (sin push, lo sube el usuario).

## Riesgos
- **Ruff con 0 errores en todo el repo**: puede haber muchos hallazgos; `--fix` resuelve la mayoría (imports no usados, formato). Los restantes se corrigen a mano o se ignoran con `# noqa` justificado. Riesgo de regresión → se verifica con suite completa.
- **Bandit ruidoso**: se configura `skip` de tests/fixtures y umbral severidad medio+.
- **pip-audit falla por vuln sin fix disponible**: se documenta en spec; el workflow reporta pero no debe romper indefinidamente sin criterio (se evalúa al implementar).

## Verificación
- `ruff check .` → 0 errores.
- `python manage.py check` → OK.
- `python manage.py test` → 283 OK.
- YAMLs validados (actionlint o revisión manual).
