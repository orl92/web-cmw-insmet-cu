```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:d602eafcba6ff8565bd64828cdbe2092fdca32fd6588e1bbf71abcbf9ea7d6c4
verdict: pass
blockers: 0
critical_findings: 0
requirements: 2/2
scenarios: 16/16
test_command: source .venv/bin/activate && python manage.py test apps.home --parallel -v 0
test_exit_code: 0
test_output_hash: sha256:3ba2b66074397dc6048109ce1a0219649614367b9ff1f154827662c6a5f167e7
build_command: source .venv/bin/activate && python manage.py check
build_exit_code: 0
build_output_hash: sha256:1e3e63f221bde88816c4a4ef7367691607b20cc1d194028a02ec9ae0586cf9b1
```

## Verification Report

**Change**: layout-cards-servicios
**Version**: spec delta v1 (2 deltas: `home-public-services-layout`, `customer-services-dashboard` REQ-05)
**Mode**: Strict TDD (`openspec/config.yaml` `testing.strict_tdd: true`; módulo `strict-tdd-verify.md` cargado)
**Store**: openspec — `openspec/changes/layout-cards-servicios/`

### Completeness

| Métrica | Valor |
|---|---|
| Tasks total | 14 |
| Tasks completas | 14 |
| Tasks incompletas | 0 |
| Requisitos (specs delta) | 2 (1 `### Requirement:` + 1 `### REQ-05:`) |
| Escenarios | 16 |
| Escenarios COMPLIANT | 16 |
| Escenarios PARTIAL | 0 |
| Escenarios UNTESTED | 0 |

### Build & Tests Execution

**Build (Django check)**: ✅ Passed — exit 0 — `System check identified no issues (0 silenced).`

**Tests (enfocado)**: ✅ 61 passed / ❌ 0 failed / 0 skipped — `python manage.py test apps.home.tests.test_services_ui -v 0` → `Ran 61 tests in 18.695s` → `OK` (exit 0)

**Tests (suite `apps.home --parallel`)**: ✅ 189 passed / ❌ 0 failed / 0 skipped — `python manage.py test apps.home --parallel -v 0` → `Ran 189 tests in 61.549s` → `OK` (exit 0). El baseline rojo documentado en design.md (`test_calendar_icon_precedes_date_range_in_dom`, `test_metadata_layout_order_is_dates_payment_price`) queda VERDE.

**djlint**: ✅ `--reformat --check` → "0 files would be updated." (exit 0) · `--lint` → "Linted 2 files, found 0 errors." (exit 0) — 2/2 templates del cambio.

| Evidencia | Valor |
|---|---|
| test_command (enfocado) | `source .venv/bin/activate && python manage.py test apps.home.tests.test_services_ui -v 0` |
| test_exit_code (enfocado) | 0 |
| test_output_hash (enfocado) | sha256:3740b4140582547b712d3855220749a9c7e96de1fb6ac6ba70e3a180460e8b12 |
| test_command (suite) | `source .venv/bin/activate && python manage.py test apps.home --parallel -v 0` |
| test_exit_code (suite) | 0 |
| test_output_hash (suite) | sha256:3ba2b66074397dc6048109ce1a0219649614367b9ff1f154827662c6a5f167e7 |
| build_command | `source .venv/bin/activate && python manage.py check` |
| build_exit_code | 0 |
| build_output_hash | sha256:1e3e63f221bde88816c4a4ef7367691607b20cc1d194028a02ec9ae0586cf9b1 |
| djlint_reformat_exit_code | 0 |
| djlint_reformat_output_hash | sha256:ae295eceef0bdbdaf0f5a5137b8aa88e3a30cd46a4ec266cdd91df2740d3b98e |
| djlint_lint_exit_code | 0 |
| djlint_lint_output_hash | sha256:f5a621ce2b1fcba277b6f9f86fdc4338ca6874fe7de9e87bc78f33e388dc1710 |
| ruff_check_exit_code | 1 (E501 — ver Issues) |

**Coverage**: ➖ No hay tool de coverage configurada (`config.yaml` `coverage_tool: none`; no es fallo).

### Spec Compliance Matrix

#### home-public-services-layout (Requirement: Commercial services public card is state-neutral)

| Escenario | Test | Resultado |
|---|---|---|
| S1 Card sin ribbon ni botones de estado | `ServiceReRequestUiTests.test_public_list_active_shows_state_neutral_card` + `test_public_list_state_neutral_regardless_of_subscription_state` + `test_pending_non_qr_public_catalog_is_state_neutral` | ✅ COMPLIANT |
| S2 Card anónimo sin ribbon | `ServicesCommercialStaffButtonTests.test_anonymous_sees_login_cta_only_and_no_ribbon` | ✅ COMPLIANT |
| S3 Precio sin icono dollar | `CommercialCatalogCodeAndCategoryUITests.test_catalog_no_currency_dollar_icon` | ✅ COMPLIANT |
| S4 Sin bloque código | `test_catalog_shows_category_badge_and_code` + `test_catalog_hides_code_label_when_service_has_no_code` | ✅ COMPLIANT |
| S5 Badge categoría pronóstico con icono | `test_catalog_category_badge_has_cloud_icon` (actualizado: `ti-cloud` con `me-1` ANTES de "Categoría:" en su línea `<div class="mb-2">` + `<strong>Pronóstico</strong>`) | ✅ COMPLIANT |
| S6 Badge categoría agrometeo con icono | `test_catalog_category_badge_has_plant_icon` (actualizado: ídem con `ti-plant` + `<strong>Agrometeorológico</strong>`) | ✅ COMPLIANT |
| S7 Orden DOM categoría-período-precio | `test_catalog_dom_order_category_period_price` (nuevo: categoría < período < precio en wrapper, sin `d-flex flex-wrap gap-2`) | ✅ COMPLIANT |
| S8 Precio destacado display-6 con CUP/período | `test_catalog_price_uses_display6_highlight` (nuevo: `display-6 fw-bold text-primary` + `$100,00` + `<small class="text-secondary">CUP/mes</small>`) | ✅ COMPLIANT |
| S9 Icono de categoría antes del label | `test_catalog_category_badge_has_cloud_icon` (`me-1` index < "Categoría:" index en la línea `mb-2`; `<strong>{{ get_service_category_display }}</strong>`) | ✅ COMPLIANT |

#### customer-services-dashboard (REQ-05: Metadatos normalizados)

| Escenario | Test | Resultado |
|---|---|---|
| S1 Calendario precede al rango | `CommercialServicesListViewStateScopeTests.test_calendar_icon_precedes_date_range_in_dom` (baseline rojo ahora verde: `ti-calendar-month` corregido en `commercial.html` L33) | ✅ COMPLIANT |
| S2 Precio sin icono dollar ni duplicación de período | `test_subscription_no_dollar_icon_in_price` + `test_subscription_price_no_suffix` (nuevo: display-6 + `$10,00` + assertNotIn `CUP/` en región metadata) | ✅ COMPLIANT |
| S3 Orden DOM fechas-pago-categoría-período-precio | `test_metadata_layout_order_is_dates_payment_price` (re-escopado al wrapper `d-flex flex-column flex-grow-1 text-secondary mb-3`; 5 marcadores en orden; sin `flex-wrap gap-2`; sin `CUP/`) | ✅ COMPLIANT |
| S4 Líneas de categoría y período con strong | `test_subscription_lines_have_strong` (nuevo: `Categoría: <strong>Pronóstico</strong>` + `Período: <strong>día</strong>`) | ✅ COMPLIANT |
| S5 Icono de pago diferenciado antes del texto | `test_subscription_payment_icon_presencial` (nuevo: `ti-building-store` con `me-1` ANTES de "Pago Presencial" en su línea `mb-2`) + `test_subscription_payment_icon_qr` + `test_subscription_payment_icon_transfer` + unit `PaymentMethodIconFilterTests` (mapeo exacto qr/transfer/presencial) | ✅ COMPLIANT |
| S6 Sin método de pago se omite la línea | `test_subscription_no_payment_method_omits_line` (nuevo: ausencia de los 4 iconos de pago en región metadata; fechas/categoría/período presentes) | ✅ COMPLIANT |
| S7 Precio destacado solo comercial | `test_subscription_commercial_only_price_highlight` (nuevo: service PUBLIC sin `display-6`; fechas + período presentes) | ✅ COMPLIANT |

**Compliance summary**: 16/16 escenarios COMPLIANT, 0 PARTIAL, 0 UNTESTED

### Correctness (Evidencia estática)

| Req | Estado | Evidencia |
|---|---|---|
| home-public-services-layout | ✅ Implementado | `commercial_public.html:30-46` — wrapper `d-flex flex-column flex-grow-1 text-secondary mb-3` + 3 líneas `<div class="mb-2">` independientes (Categoría `ti-cloud`/`ti-plant` me-1 + strong; Período `ti-calendar-event` me-1 + strong; Precio `display-6 fw-bold text-primary` con `<small class="text-secondary">CUP/<período></small>`); sin `flex-wrap gap-2`; acciones conservan `mt-auto` (redundante por D1) |
| REQ-05 | ✅ Implementado | `commercial.html:31-55` — wrapper idéntico + 4-5 líneas `<div class="mb-2">` (Fechas `ti-calendar-month` me-1; Pago condicional `{% if payment_method %}` con `payment_method_icon` me-1; Categoría `ti-tag` me-1 + strong; Período `ti-calendar-event` me-1 + strong; Precio `display-6 fw-bold text-primary` SOLO monto si `service_type == 'commercial'`); `grep -c mt-auto` → 0; sin `ti-currency-dollar` |

### Coherence (Design)

| Decisión | ¿Seguida? | Notas |
|---|---|---|
| D1 Pin vertical wrapper `flex-grow-1` (sin `mt-auto` en metadata) | ✅ Sí | Ambos templates: `<div class="d-flex flex-column flex-grow-1 text-secondary mb-3">`; `grep -c 'mt-auto' commercial.html` → 0 (task 2.2); acciones del catálogo intactas con `mt-auto` redundante (D1 explícitamente lo permite) |
| D2 `display-6 fw-bold text-primary` conservado | ✅ Sí | `commercial_public.html:44` y `commercial.html:52`; QA visual 360px pendiente (pregunta abierta D2, no bloqueante) |
| D3 Estructura DOM destino | ✅ Sí | Catálogo 3 líneas exactas (D3 tabla); Mis Servicios 4-5 líneas exactas; orden DOM y wrapper tal como el design |
| Estrategia de tests | ✅ Sí | 3.1 re-escopado al wrapper + orden 5 líneas; 3.2 iconos `me-1` antes del label; nuevos 3.3/3.4 y 4.1-4.5 presentes, RED documentado y verdes en ejecución |

### TDD Compliance

| Check | Resultado | Detalles |
|---|---|---|
| TDD Evidence reported | ✅ | `apply-progress.md` declara "Modo: Strict TDD" e incluye tabla "TDD Cycle Evidence" con 14 filas (tasks 1.1-5.2) |
| All tasks have tests | ✅ | 14/14 tasks; `apps/home/tests/test_services_ui.py` existe y pasa (61 tests enfocados; 7 nuevos + 2 baseline RED ahora verdes) |
| RED confirmed (tests exist) | ✅ | apply-progress reporta fase RED: 11 fallos (3 failures + 8 errors) contra los templates viejos; safety net de 54 tests con exactamente los 2 RED documentados en design.md |
| GREEN confirmed (tests pass) | ✅ | 61/61 enfocado + 189/189 suite `apps.home` en ejecución real (ambos exit 0) |
| Triangulation | ✅ | 3.2 por 2 categorías (cloud/plant); 3.4 agrometeo `CUP/mes`; 4.2 presencial (qr/transfer ya cubiertos por baseline); 4.4 public vs commercial (caso opuesto en 3.1/4.5); 4.3 presencia vs ausencia — expectativas con valores distintos |
| Safety Net para archivos modificados | ✅ | apply-progress: 54 tests corriendo pre-cambio (2 RED conocidos del baseline); post-cambio 61 → 189 en suite |

**TDD Compliance**: 6/6 checks completos.

### Test Layer Distribution

| Capa | Tests | Archivos | Herramientas |
|---|---|---|---|
| Unit | 5 (`PaymentMethodIconFilterTests` — mapeo exacto del filtro) | 1 | unittest Django |
| Integration | 56 (resto de `test_services_ui.py`: 61 − 5) | 1 | Django test Client (render real con middleware + context processors) |
| E2E | 0 | — | no aplica (sin tooling E2E en el proyecto) |
| **Total (archivo del cambio)** | **61** | **1** | dentro de **189** (suite `apps.home --parallel`) |

### Changed File Coverage

Coverage tool no disponible (`config.yaml` `coverage_tool: none`). Análisis cualitativo: los 61 tests renderizan las vistas/templates modificados con el stack real; 16/16 escenarios tienen test que pasa en runtime cubriendo ambos templates. No se reporta % de líneas.

### Assertion Quality

**Assertion quality**: ✅ All assertions verify real behavior — 0 tautologías, 0 ghost loops, 0 smoke tests, 0 aserciones tipo-only.

- Aserciones de HTML real renderizado: orden DOM inter-span vía índices relativos en scope metadata (`meta_start`/`meta_end` delimitado por marcadores reales), clases CSS exactas (`display-6 fw-bold text-primary`, `mb-2`, `me-1`), ausencias scoped (`assertNotIn` sobre la región metadata, no el HTML completo), textos exactos (`$1.234,56`, `CUP/mes`, `Categoría: <strong>Pronóstico</strong>`).
- Ghost-loop check: los loops de ausencia (4.3) iteran sobre lista constante de 4 iconos y dependen de `html.index()` que lanza si el marcador falta — nunca un ciclo silencioso.
- Triangulación con expectativas distintas: cloud vs plant; `CUP/día` vs `CUP/mes` (fixtures distintos); $ vs ausencia de `display-6`; presencia vs ausencia de línea de pago.

### Quality Metrics

**Linter (ruff)**: ⚠️ 1 error — E501 (line too long 119 > 100) en `apps/home/tests/test_services_ui.py:737`, introducido por el test nuevo 3.4 (`test_catalog_price_uses_display6_highlight`). Auto-fixable por ruff-format del pre-commit, pero conviene corregirlo antes de commitear.
**Formatter (ruff format)**: ➖ no ejecutado.
**Type Checker**: ➖ No disponible (`config.yaml` `type_checker: none`).
**Template linter (djlint)**: ✅ `--lint` 0 errores, `--reformat --check` 0 archivos a actualizar (2/2 templates del cambio).

### Issues Found

**CRITICAL**: None

**WARNING**:

1. **E501 en `test_services_ui.py:737`** — línea de 119 > 100 chars introducida por el test nuevo 3.4. `ruff check` exit 1. Auto-fixable por `ruff-format` del pre-commit, pero corregir a mano antes del commit evita un hook-fix implícito.
2. **Prosa de spec vs decisión D1 (divergencia documentada)**: ambas specs dicen que el último bloque de metadata SHALL conservar `mt-auto mb-3`; el diseño (D1) y la implementación usan wrapper `flex-grow-1` + `mb-3` sin `mt-auto` en la metadata (el catálogo conserva `mt-auto` solo en acciones). Ningún escenario aserta `mt-auto` y la reconciliación está documentada en `design.md:21`; 16/16 tests pasan. Alinear la prosa de la spec con el diseño al promover en archive.
3. **Cobertura de variantes REQ-05 S5**: el aserto completo `me-1` ANTES del texto solo se ejecuta para presencial; las variantes QR/transfer asertan presencia del icono + mapeo unit del filtro. El patrón del template es uniforme (`me-1` en las 3), así que no es fallo; un aserto de orden para QR añadiría robustez.

**SUGGESTION**:

1. **Quirk preexistente `default_if_none:'—'` inerte** (catálogo): `format_cup(None)` devuelve `'$0,00'`, nunca `None`, así que el fallback `—` no se activa. Fuera de scope (documentado en apply-progress); puede simplificarse en un cambio futuro.
2. **QA visual de `display-6` a 360px pendiente** (pregunta abierta D2 del design): la clase es fluid en Tabler; si desborda en viewports estrechos, escalar a revisión de specs — no cambiar la clase en silencio.

### Verdict

**PASS**

16/16 escenarios COMPLIANT con evidencia runtime (61 tests enfocados + 189 suite `apps.home`, ambos exit 0), `manage.py check` 0 issues, djlint 0 errores. Baseline rojo resuelto (`ti-calendar-month`, `test_calendar_icon_precedes_date_range_in_dom` verde). Wrapper `d-flex flex-column flex-grow-1 text-secondary mb-3` y líneas `mb-2` independientes exactos en ambos templates (3 líneas catálogo, 4-5 Mis Servicios). TDD 6/6 con evidencia RED→GREEN→triangulación en apply-progress. WARNINGs no bloqueantes: E501 nuevo en test (auto-fixable), prosa `mt-auto mb-3` de specs vs D1 documentado, cobertura parcial de variantes QR/transfer (patrón uniforme).

### Next Recommended

**archive**: requisitos (2/2), escenarios (16/16) y tasks (14/14) completos. La fase archive debe promover los specs y archivar el cambio; al promover, alinear la prosa `mt-auto mb-3` con el mecanismo real del wrapper `flex-grow-1` (D1) y corregir el E501 previo al commit.
