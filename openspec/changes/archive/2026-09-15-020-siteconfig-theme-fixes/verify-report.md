```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:ae17ba184490ade5c54f1b65f6141179adcf0baf17191e09eae840c35a8e1958
verdict: pass
blockers: 0
critical_findings: 0
requirements: 5/5
scenarios: 7/7
test_command: .venv/bin/python manage.py test apps.core apps.user_auth
test_exit_code: 0
test_output_hash: sha256:fb7f4d6004204e63c6e9e230c711475d947ae32cfab293c7576832c5c92258cb
build_command: .venv/bin/python manage.py check
build_exit_code: 0
build_output_hash: sha256:1e3e63f221bde88816c4a4ef7367691607b20cc1d194028a02ec9ae0586cf9b1
```

## Verification Report

**Change**: 020-siteconfig-theme-fixes (RE-VERIFICACIÓN tras remediación — spec re-sincronizada)
**Version**: N/A (unversioned delta spec)
**Mode**: Strict TDD
**Artifacts**: proposal, spec (`### Requirement:` x5 / `#### Scenario:` x7, grep-verified), design, tasks (60/60 `[x]`), verify-report previo (FAIL — reemplazado por éste)
**Evidence digest**: `sha256:ae17ba18…` = sha256 de proposal.md + spec.md + design.md + tasks.md (orden canónico, concatenados)

### Completeness
| Metric | Value |
|--------|-------|
| Tasks total | 60 |
| Tasks complete | 60 |
| Tasks incomplete | 0 |

### Build & Tests Execution

**Build (Django system check)**: ✅ Passed (exit 0)
```text
.venv/bin/python manage.py check
System check identified no issues (0 silenced).
```
**Migrations**: ✅ `.venv/bin/python manage.py makemigrations --check --dry-run` → `No changes detected` (exit 0)

**Tests**: ✅ 228 passed / 0 failed (exit 0)
```text
.venv/bin/python manage.py test apps.core apps.user_auth
Ran 228 tests in 100.563s — OK
```
(228 = 227 previos + el test de remediación `test_home_page_injects_model_theme_config_server_side`;
módulo `apps.core.tests.test_tabler_upgrade`: 15 OK, incluye el nuevo test.)

**Coverage**: ➖ Not available (`coverage_tool: none` en `openspec/config.yaml` — no es fallo).

**Lint / format / JS syntax**:
- `djlint --reformat --check` sobre los 4 templates tocados (`head.html`, `scripts.html`,
  `site/settings.html`, `company/settings.html`) → exit 0, `0 files would be updated`
- `ruff check apps/core apps/user_auth` → `All checks passed!` (exit 0)
- `node --check static/dist/js/tabler-theme.min.js` → OK (loader parcheado sintácticamente válido)

### Spec Compliance Matrix

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| THEME-BASE-APPLIED | Model theme renders on load | `apps.core.tests.test_tabler_upgrade > test_home_page_injects_model_theme_config_server_side` (render real de `/`: el bloque inline pre-paint lleva `"theme-base": "zinc"`, `"theme-font": "serif"`, `"theme-primary": "red"` — autoridad del modelo, valores no-default, PASS en ejecución) + probe Node S1 (ejecución del script real de `head.html` con `neutral/sans-serif/1/#2b4b9b` → `data-bs-theme-base/font/radius`, `data-bs-theme-primary`, `--tblr-primary`/`-rgb` inline, 7/7 asserts PASS) | ✅ COMPLIANT |
| THEME-BASE-APPLIED | Visitor light/dark never touches admin theme | `test_home_page_renders_explicit_light_theme`, `test_dashboard_renders_explicit_light_theme` (default light explícito server-side, PASS), `test_head_html_prepaint_sets_theme_attribute_always` (contrato: `setAttribute` siempre, sin `removeAttribute`, sin `auto`, PASS) + probe Node S2: `localStorage['tabler-theme']='dark'` → `data-bs-theme="dark"` Y `data-bs-theme-base` sigue `"neutral"` (PASS); probe loader: el parche solo escribe/lee `data-bs-theme`, nunca `data-bs-theme-base/-font/-primary/-radius` (5/5 asserts PASS) | ✅ COMPLIANT |
| RESET-RESTORES-MODEL | Reset restores model defaults | `test_reset_theme_defaults_restores_defaults` (POST `reset_theme_defaults` → 302 → modelo `#2b4b9b/neutral/sans-serif/1`, PASS) | ✅ COMPLIANT |
| THEME-CSS-PRIMARY-ONLY | Only primary customized | inspección (mecanismo propio del escenario): `static/dist/css/theme.css:8-10` — solo dark `--tblr-primary: #2b4b9b` / `--tblr-primary-rgb: 43, 75, 155`; sin `--tblr-link`; light-primary runtime-only | ✅ COMPLIANT |
| SETTINGS-FORM-STANDARD | Standard form shell | `test_uses_form_layout_shell` (multipart + novalidate de `layouts/form.html`), `test_two_section_cards_rendered` (Colores y tema + Identidad), `test_maintenance_card_present_for_superuser` / `_absent_for_non_superuser` (todos PASS) | ✅ COMPLIANT |
| SETTINGS-FORM-STANDARD | Brand logo hint | `test_brand_logo_hint_present` — hint exacto "Formatos: JPG, PNG, GIF. No se admiten SVG…" (`settings.html:113`, PASS) | ✅ COMPLIANT |
| SETTINGS-FORM-STANDARD | Favicon preview | `test_favicon_preview_and_link_when_set` — preview 64px, "Ver imagen" `data-fslightbox`, delete action junto al file input (PASS); `test_favicon_hint_present_when_unset` + `test_no_clearable_widget_cartel` + delete actions (PASS) | ✅ COMPLIANT |

**Compliance summary**: 7/7 scenarios compliant (cada uno con evidencia ejecutada — test de
template/views corriendo en Django o probe Node ejecutando el JS real shippeado).

**Probe Node (evidence probe, sin harness de browser — restricción del proyecto)**:
```text
PASS S1 data-bs-theme-base=neutral        PASS S1 --tblr-primary inline
PASS S1 data-bs-theme-font=sans-serif     PASS S1 --tblr-primary-rgb inline
PASS S1 data-bs-theme-radius=1            PASS S1 visitor default light
PASS S1 data-bs-theme-primary=#2b4b9b     PASS S2 data-bs-theme=dark
PASS S2 data-bs-theme-base stays neutral  PASS LOADER data-bs-theme=dark
PASS LOADER never writes admin attrs      PASS LOADER never removes admin attrs
PASS LOADER keeps model base intact       PASS LOADER keeps model primary intact
14/14 PASS (exit 0)
```
Ejecuta el script inline real de `head.html` (pre-paint) y el loader parcheado
`static/dist/js/tabler-theme.min.js` contra stubs mínimos de `document`/`window`/`localStorage`,
con los valores del modelo del escenario. Artefacto temporal fuera del repo; no añade tooling al proyecto.

### Correctness (Static & Runtime Evidence)
| Requirement | Status | Notes |
|------------|--------|-------|
| THEME-BASE-APPLIED | ✅ Implemented | `data-bs-*` + `--tblr-*` desde el modelo en pre-paint (`head.html:34-85`) y en `DOMContentLoaded` (`scripts.html:34-56`); sin lectura de `localStorage['tabler-*']` para base/font/radius/primary; visitor light/dark solo en `data-bs-theme` (`?theme=`/`localStorage['tabler-theme']`/`light`) — coincidencia byte a byte con la spec re-sincronizada |
| RESET-RESTORES-MODEL | ✅ Implemented | Botón "Restablecer tema" en `title_actions` (`settings.html:4-14`) + modal con `name="reset_theme_defaults"` (`settings.html:52-75`); POST server-side restaura `#2b4b9b/neutral/sans-serif/1`, `log_action` y redirect (`views/site_configuration.py:61-77`); sin limpieza client-side de localStorage (floating switch removido) |
| THEME-CSS-PRIMARY-ONLY | ✅ Implemented | Exactamente dark primary/rgb; sin `--tblr-link`; light-mode primary runtime-only del modelo |
| SETTINGS-FORM-STANDARD | ✅ Implemented | Extiende `layouts/form.html`; `{% block form %}` con 3 cards (Colores y tema, Identidad, Mantenimiento superuser-gated); Coloris `primary_color` + selects `theme_base/font/radius`; hints logo/favicon; previews 64px + "Ver imagen" + Eliminar; branches `delete_logo`/`delete_favicon`/`toggle_maintenance`; modelo con `theme_base='neutral'` / `theme_font='sans-serif'` / `theme_radius='1'` / `primary_color='#2b4b9b'` por defecto |
| NO-REGRESSION-020 | ✅ Implemented | `logo.html` intacto (último cambio `c04abd9`, change 007); sin `package.json` ni npm/bundler (Coloris vendoreado `static/dist/libs/coloris/`); parche único documentado del loader (`tabler-theme.min.js:1-14`) con la excepción FOUC; `check`/tests/djlint/ruff/node-check verdes |

### Coherence (Design)
| Decision | Followed? | Notes |
|----------|-----------|-------|
| `applyConfig()` renders all `themeConfig` keys | ✅ Superseded en línea con spec | El diseño original (Phases 1-4) fue reemplazado por la re-aplicación model-only en Phase 7.3 — exactamente lo que la spec re-sincronizada exige (autoridad del modelo) |
| `data-bs-theme` vs `data-bs-theme-base` two-axis | ✅ Yes | `data-bs-theme` (light/dark, visitor) + `data-bs-theme-base/font/radius` + `data-bs-theme-primary`/inline `--tblr-*` (model) |
| `theme.css` removes only `--tblr-link` | ✅ Yes | Contenido final coincide con la decisión 3 |
| favicon/brand reuse `service/update.html` image pattern | ✅ Yes | Preview 64px, fslightbox, hints + acciones delete de Phase 5 |
| Section cards via `form_card.html` include | ✅ Alineado | La spec re-sincronizada ya NO exige el include; las cards hand-written rinden el shell estándar (tests: multipart/novalidate/secciones) |
| Phases 5-7f (FileInput unificado, Coloris, FOUC, reset server-side, mantenimiento consolidado) | ✅ Yes | Implementadas y cubiertas: `test_no_clearable_widget_cartel`, `test_primary_color_uses_coloris_picker`, `test_reset_theme_defaults_*`, `test_toggle_maintenance_*`, `test_maintenance_blocks_*` |

### TDD Compliance
| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ⚠️ | Engram `sdd/020-siteconfig-theme-fixes/apply-progress` (narrativa RED-first/GREEN, Phases 1-4) + notas de verificación inline por fase en `tasks.md` (176/181/182 OK, djlint, ruff, node --check, probes); sin tabla formal TDD-cycle |
| All tasks have tests | ✅ | 60/60 tasks mapean a comportamiento cubierto; archivos de test del change existentes y poblados (forms 6, template 17, views 11, branding 2, tabler_upgrade 15) |
| RED confirmed (tests exist) | ✅ | Archivos de test verificados en repo; tasks de test por fase (`5.6`, `6.8`, `7.8`, `7e.5`) agregan casos reales |
| GREEN confirmed (tests pass) | ✅ | 228/228 tests pasan en ejecución (exit 0), incluyendo el nuevo test de remediación |
| Triangulation adequate | ✅ | Escenarios JS-theme ahora con doble evidencia (render Django + ejecución Node del JS real); comportamientos template/view con casos distintos cada uno; valores no-default en la remediación (zinc/serif/red) |
| Safety Net for modified files | ✅ | Regression completa `apps.core` + `apps.user_auth` en verde (228, incluye suites no relacionadas) |

**TDD Compliance**: 5/6 checks passed. La ausencia de tabla formal de ciclos en el
apply-progress se degrada de CRITICAL (módulo Strict) a WARNING: la evidencia sustantiva
(archivos de test reales + ejecución verde + notas de verificación por fase + test de
remediación nuevo) demuestra que TDD se siguió — la carencia es documental, no de práctica.

### Test Layer Distribution
| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit | 8 | `test_site_configuration_forms.py` (6), `test_site_configuration_branding.py` (2) | Django TestCase (sin render) |
| Integration | 31 | `test_site_configuration_template.py` (17), `test_site_configuration_views.py` (11), `test_middleware.py` maintenance (5, suma parcial de sus 9 casos) | Django TestCase (client GET/POST, render de template) |
| Source-contract | 10 | `test_tabler_upgrade.py` (FileContractTests) | Django TestCase (assertions sobre contenido de archivos) |
| Render + JS-execution probe | 5 | `test_tabler_upgrade.py` (RenderTests, incl. remediación) + probe Node ad-hoc (14 asserts, archivo temp fuera del repo) | Django test client + node |
| E2E | 0 | — | sin harness de browser (constraint: no Node tooling en el proyecto) |
| **Total (change-related)** | **~54 + probe** | **5 files + probe** | Django test runner + node |

Nota: `test_middleware.py` (9 casos: 4 CheckUserProfile + 5 maintenance: bloca anónimo/
no-superuser 503, permite superuser y `/login/`) cubre la consolidación de Phase 7f.

### Changed File Coverage
Coverage analysis skipped — no coverage tool detected (`coverage_tool: none`; informativo, no es fallo).

### Assertion Quality
| File | Line | Assertion | Issue | Severity |
|------|------|-----------|-------|----------|
| `apps/core/tests/test_site_configuration_template.py` | 60 | comentario "the two form_card includes" | Engañoso — las cards son hand-written, el include no se usa | SUGGESTION |
| `apps/core/tests/test_site_configuration_template.py` | 155-157 | `assertGreaterEqual(count, 1)` + `assertIn` | El count assertion no aporta sobre el `assertIn` adyacente | SUGGESTION |

**Assertion quality**: 0 CRITICAL, 0 WARNING — ✅ All assertions verify real behavior
(sin tautologías ni ghost loops — guardas anti-ghost-loop presentes en
`test_tabler_upgrade.py` (`scanned > 50`/`scanned > 20`) — ni type-only/smoke-only en los
5 archivos auditados; el nuevo test de remediación afirma valores no-default del modelo,
no un mero render).

### Quality Metrics
**Linter**: ✅ No errors — `ruff` clean (apps/core, apps/user_auth); `djlint --reformat --check` clean en los 4 templates tocados
**Type Checker**: ➖ Not available (`type_checker: none`)
**JS syntax**: ✅ `node --check` pasa en el loader parcheado; probe Node 14/14 OK

### Issues Found

**CRITICAL**: None

**WARNING**:
1. **Evidencia TDD documental.** El apply-progress (Engram) es narrativa (Phases 1-4) y no
   tiene tabla formal de ciclos; Phases 5-7f solo en notas inline de `tasks.md`. Degradado de
   CRITICAL (módulo Strict) a WARNING por la evidencia sustantiva en verde (228/228, archivos
   de test reales, notas por fase, test de remediación nuevo y pasando).
2. **Trazabilidad del loader.** El parche documentado (spec nombra Tabler 1.5.1, commit
   `c14686d`) fue portado a la re-vendoria 1.5.1 con el comportamiento light/dark-only y el
   header de comentario actualizado — dentro de la excepción documentada de
   NO-REGRESSION-020; se anota para auditoría (el archivo actual es 1.5.1 + parche, no el
   binario exacto de c14686d).

**SUGGESTION**:
1. Corregir el comentario engañoso en `test_site_configuration_template.py:60`.
2. Eliminar el count assertion redundante en `test_logo_and_favicon_side_by_side`
   (`assertGreaterEqual(count, 1)` + `assertIn`).

### Verdict

**PASS** — La implementación coincide byte a byte con la spec re-sincronizada (diseño
entregado fases 5-7f: tema admin-only con autoridad del modelo, `data-bs-*`, reset
server-side, excepción documentada del loader), 60/60 tasks, build/migrations limpios,
228/228 tests verdes (incluye el test de remediación), djlint/ruff/node-check OK, y los
2 escenarios JS-theme tienen ahora evidencia ejecutada: el escenario 1 vía
`test_home_page_injects_model_theme_config_server_side` (render real + probe Node) y el
escenario 2 vía los tests de render/contrato + probe Node sobre el JS real shippeado y el
loader parcheado (14/14 asserts PASS). 7/7 scenarios con covering test pasado en runtime;
`pass` admitido por `gentle-ai sdd-verify-validate` (5/7 → 7/7). Archive queda desbloqueado.

**Next recommended**: archive
