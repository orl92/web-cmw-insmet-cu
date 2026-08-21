# Spec — 084-formato-templates-djlint

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
