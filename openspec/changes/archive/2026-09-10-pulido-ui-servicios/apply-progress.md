# Apply Progress: Pulido UI Servicios

## Status
- **applyState**: all_done
- **Mode**: STRICT TDD (`openspec/config.yaml` `testing.strict_tdd: true`; runner `python manage.py test apps.<app>`)
- **Tasks**: 23/23 complete + remediación post-verify (R1-R5, 3 escenarios UNTESTED cubiertos)

> Corrección de CRITICAL 4 del verify: la versión previa de este artefacto declaraba
> "Mode: Standard (no strict_tdd)" y omitía la tabla TDD Cycle Evidence. El modo real
> del cambio es STRICT TDD según `config.yaml`; la evidencia del protocolo se reporta
> abajo con ejecuciones reales (comandos y salidas).

## Completed Tasks

### Phase 1: Templatetag + Vista
- [x] 1.1 `payment_method_icon` filter in `utils_filters.py`
- [x] 1.2 `latest_invoice` in `CommercialServicesListView.get_context_data`

### Phase 2: Templates Menú + Card
- [x] 2.1 Dot animado → badge `bg-red-lt` en toggle padre Servicios
- [x] 2.2 Badges eliminados de "Servicios Comerciales"
- [x] 2.3 Badges requested/pending migrados a "Mis Servicios"
- [x] 2.4 `ti-credit-card` → `payment_method_icon` filter
- [x] 2.5 `ti-currency-dollar` eliminado del precio
- [x] 2.6 "Ver factura" condicionado a `latest_invoice`, uuid URL

### Phase 3: Catálogo Público + Error Pages
- [x] 3.1 Iconos diferenciados en badge categoría
- [x] 3.2 `ti-currency-dollar` eliminado del catálogo
- [x] 3.3 Bloque "Código:" eliminado
- [x] 3.4 `history.back()` en 400.html
- [x] 3.5 `history.back()` en 403.html
- [x] 3.6 `history.back()` en 404.html
- [x] 3.7 `history.back()` en 500.html

### Phase 4: Tests
- [x] 4.1 Tests menu dot animado actualizados
- [x] 4.2 Tests menu hidden actualizados
- [x] 4.3 Test pending qr actualizado
- [x] 4.4 Test pending transfer actualizado
- [x] 4.5 Tests nuevos: payment method icon, catalog icons, error pages

### Phase 5: Verificación Final
- [x] 5.1 `manage.py check` OK, `manage.py test apps.home apps.commercial apps.core` 545/545 OK (verify, hash `be893a43…`)
- [x] 5.2 `djlint --reformat --check` clean sobre templates del cambio, `djlint --lint` 0 errores
- [x] 5.3 `gentle-ai sdd-status` reports tasks: present

### Remediation (post-verify FAIL — 3 escenarios UNTESTED + E501 + evidencia)
- [x] R1 REQ-09 S4 — `test_services_commercial_menu_item_has_no_state_badges` (`test_services_ui.py:894`)
- [x] R2 REQ-04 S2 — `test_pending_subscription_without_invoice_hides_invoice_button` (`test_services_ui.py:432`)
- [x] R3 REQ-05 S3 — `test_metadata_layout_order_is_dates_payment_price` (`test_services_ui.py:315`)
- [x] R4 ruff E501 (`test_services_ui.py:932` `test_error_403_template_has_history_back`, línea 106 → ≤100) + `ruff format` solo sobre `test_services_ui.py`
- [x] R5 Evidencia TDD reportada en este artefacto (modo correcto, tabla abajo)

## TDD Cycle Evidence

Runner: `python manage.py test apps.<app>` (Django unittest, `config.yaml`). Safety Net
baseline pre-remediación: `python manage.py test apps.home.tests.test_services_ui
apps.core.tests.test_context_processors` → **53 OK** (exit 0). Suite selectiva del
verify (apps.home+apps.commercial+apps.core): **545/545 OK**, exit 0, hash de salida
`be893a43769b3d738d79a7aeec866be5b3d319ab366c4ce204bb123a67e62113`.

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1-1.2 (filter + contexto vista) | `test_services_ui.py` (`PaymentMethodIconFilterTests`) | Unit | ✅ suite previa OK | ✅ 5 unit tests del mapeo escritos primero (qr/transfer/presencial/default/None) | ✅ 545/545 (verify) + re-run 2026-09-10 | ✅ 5 inputs distintos (incl. unknown y None) | ✅ Clean |
| 2.1-2.6 (menú + card) | `test_services_ui.py` (`MisServiciosMenuItemTests`, `CommercialServicesListContextualActionsTests`) | Integration | ✅ suite previa OK | ✅ asserts badge `bg-red-lt`/`bg-blue-lt`/`bg-orange-lt`, `assertNotIn status-dot`, URL `factura/<uuid>/pdf/?inline=1` | ✅ 545/545 (verify) | ✅ fixture con y sin acciones pendientes (1+1=2 y 0) | ✅ djlint clean |
| 3.1-3.7 (catálogo + error pages) | `test_services_ui.py` (catalog tests, `ErrorPagesHistoryBackTests`) | Integration | ✅ suite previa OK | ✅ asserts `ti-cloud`/`ti-plant`, ausencia `ti-currency-dollar`/`Código:`, `history.back()` + guard | ✅ 545/545 (verify) | ✅ pronóstico + agrometeo; con y sin código; 4 layouts | ✅ djlint clean |
| 4.1-4.5 (tests) | `test_services_ui.py` | Unit + Integration | ✅ suite previa OK | ✅ 5 métodos actualizados + 8 métodos nuevos sobre comportamiento | ✅ 545/545 (verify) | ✅ cobertura de todos los estados y métodos de pago | ✅ Clean |
| 5.1-5.3 (verificación) | — | N/A | ✅ previa OK | ➖ N/A (sin código nuevo) | ✅ check 0 issues; suite 545 OK | ➖ Single | ✅ — |
| R1 REQ-09 S4 | `test_services_ui.py:894` | Integration | ✅ 53 OK pre-edit | ✅ ausencia `badge`/`bg-blue-lt`/`bg-orange-lt` scoped al anchor `services_commercial_public` + `count(...) == 1` | ✅ 56 OK → 54/54 (post-format run 2026-09-10) | ✅ assertIn badges en "Mis Servicios" (mismo fixture) — la ausencia es específica del item | ✅ ruff format clean |
| R2 REQ-04 S2 | `test_services_ui.py:432` | Integration | ✅ 53 OK pre-edit | ✅ `assertNotIn('Ver factura'|'/factura/'|'ti ti-receipt')` con pending+qr sin invoices | ✅ 56 OK → 54/54 | ✅ contra `test_pending_qr_offers…` (con invoice): presencia vs ausencia | ✅ ruff format clean |
| R3 REQ-05 S3 | `test_services_ui.py:315` | Integration | ✅ 53 OK pre-edit | ✅ índices DOM relativos fechas < pago < precio (scope región metadata) | ✅ 56 OK → 54/54 | ✅ contra `test_calendar_icon_precedes…` (orden intra-span, ya existente) | ✅ ruff format clean |
| R4 E501 + format | `test_services_ui.py:932` | N/A (linter) | ✅ E501 106>100 detectado pre-edit | ✅ línea nueva ≤ 100 chars | ✅ `ruff check` → "All checks passed!" | ➖ Single | ✅ `ruff format` 1 archivo → `ruff format --check` "already formatted" |
| R5 evidencia TDD | `apply-progress.md` | N/A | ✅ verify FAIL (evidencia ausente) | ➖ N/A (artefacto de proceso) | ✅ tabla con ejecuciones reales + modo STRICT TDD declarado | ➖ Single | ✅ — |

### Test Summary (remediación R1-R4)
- **Total tests escritos**: 3 (R1-R3) + 1 línea corregida (R4)
- **Total tests pasando**: 54/54 en `test_services_ui.py`; 182/182 en `apps.home`; 53 baseline preservado
- **Layers usadas**: Integration (3)
- **Approval tests**: None — no hubo refactor de código de producción, solo tests de cobertura
- **Pure functions**: 0 nuevas (no aplica — sin lógica de producción nueva)

## Work Unit Evidence

| Evidence | Value |
|---|---|
| Focused test command | `python manage.py test apps.home.tests.test_services_ui apps.core.tests.test_context_processors` — antes: 53 OK; con los 3 tests nuevos: 56 OK; post-format: `test_services_ui` 54/54 OK |
| Runtime harness | `python manage.py check` — "System check identified no issues (0 silenced)" (exit 0); `python manage.py test apps.home` — 182/182 OK |
| Rollback boundary | `apps/home/tests/test_services_ui.py` (3 tests nuevos + línea L932) y `openspec/changes/pulido-ui-servicios/apply-progress.md` — reversibles sin tocar código de producción |

## Deviations
- Minor djlint reformat applied to 3 templates (whitespace collapsing in `<span>` content) — non-functional change, within convention.
- `djlint --reformat --check` global reporta 1 archivo vendored pre-existente fuera de alcance: `staticfiles/drf_spectacular_sidecar/swagger-ui-dist/oauth2-redirect.html` (no tocado; el verify ya reportaba 0 archivos a actualizar en los templates del cambio).
- `ruff format --check` global: `utils_filters.py:19` y `views.py:67/104` siguen con diff pre-existente del repo (fuera de alcance de este cambio, no reformateados).

## Note
`qr.html` change (enzona.cu → enzona.net) is in working tree but OUT OF SCOPE for this change — pre-existing uncommitted change.
