```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:d91350bee62a1fd932da2807de00739b69aab7f91a695ef6bed467a94925f244
verdict: pass
blockers: 0
critical_findings: 0
requirements: 5/5
scenarios: 21/21
test_command: source .venv/bin/activate && python manage.py test apps.home apps.commercial apps.core
test_exit_code: 0
test_output_hash: sha256:268d7005447750ebcab846f84217622957a6a293aa21d37bc5be75bf7a347e39
build_command: source .venv/bin/activate && python manage.py check
build_exit_code: 0
build_output_hash: sha256:1e3e63f221bde88816c4a4ef7367691607b20cc1d194028a02ec9ae0586cf9b1
```

## Verification Report

**Change**: pulido-ui-servicios
**Version**: spec delta v1 (3 deltas: `customer-menu-notifications`, `customer-services-dashboard`, `home-public-services-layout`)
**Mode**: Strict TDD (`openspec/config.yaml` `testing.strict_tdd: true`; módulo `strict-tdd-verify.md` cargado)
**Store**: openspec — `openspec/changes/pulido-ui-servicios/`
**Rama/estado**: re-verify post-remediación. `qr.html` (enzona.cu → enzona.net) confirmado FUERA del diff de este cambio.

### Completeness

| Métrica | Valor |
|---|---|
| Tasks total | 23 |
| Tasks completas | 23 |
| Tasks incompletas | 0 |
| Requisitos (specs delta) | 5 (REQ-09, REQ-10, REQ-04, REQ-05 + 1 `### Requirement:` de home-public-services-layout) |
| Escenarios | 21 |
| Escenarios COMPLIANT | 21 |
| Escenarios PARTIAL | 0 |
| Escenarios UNTESTED | 0 |

### Build & Tests Execution

**Build (Django check)**: ✅ Passed — exit 0 — `System check identified no issues (0 silenced).`

**Tests**: ✅ 548 passed / ❌ 0 failed / 0 skipped — `python manage.py test apps.home apps.commercial apps.core` → `Ran 548 tests in 231.295s` → `OK` (exit 0)

**djlint**: ✅ `--lint` → "Linted 7 files, found 0 errors." (exit 0) · `--reformat --check` sobre los 7 templates del cambio → "0 files would be updated." (exit 0)

**ruff (linter de calidad)**: ✅ `ruff check apps/home/tests/test_services_ui.py` → "All checks passed!" (exit 0). E501 previo (L932, 106 > 100) remediado.

| Evidencia | Valor |
|---|---|
| test_command | `source .venv/bin/activate && python manage.py test apps.home apps.commercial apps.core` |
| test_exit_code | 0 |
| test_output_hash | `268d7005447750ebcab846f84217622957a6a293aa21d37bc5be75bf7a347e39` |
| build_command | `source .venv/bin/activate && python manage.py check` |
| build_exit_code | 0 |
| build_output_hash | `1e3e63f221bde88816c4a4ef7367691607b20cc1d194028a02ec9ae0586cf9b1` |
| djlint_lint_exit_code | 0 |
| djlint_lint_output_hash | `cac98de5de77d0d0b948d81ce2c819464cb902ab27194dbbf85cd6e312645da4` |
| djlint_reformat_exit_code | 0 |
| djlint_reformat_output_hash | `3dafcb1593dc61de1434076e1ccdb1471cf53881b4b942880c40aedf3b028128` |
| ruff_check_exit_code | 0 |

**Coverage**: ➖ No hay tool de coverage configurada (`config.yaml` `coverage_tool: none`; no es fallo).

### Spec Compliance Matrix

#### customer-menu-notifications (REQ-09, REQ-10)

| Req | Escenario | Test | Resultado |
|---|---|---|---|
| REQ-09 S1 | Badge suma requested + pending | `MisServiciosMenuItemTests.test_menu_dot_animated_shown_when_pending_actions` (badge padre `bg-red-lt ms-2">2`) | ✅ COMPLIANT |
| REQ-09 S2 | Menú visible con solo expirada | `test_menu_shows_mis_servicios_with_expired_subscription` + `test_menu_dot_animated_hidden_without_pending_actions` (badge oculto con 0 acciones) | ✅ COMPLIANT |
| REQ-09 S3 | Badges diferenciados en Mis Servicios | `test_menu_dot_animated_shown_when_pending_actions` (`bg-blue-lt ms-2">1` + `bg-orange-lt ms-2">1`) | ✅ COMPLIANT |
| REQ-09 S4 | Servicios Comerciales sin badges | `test_services_commercial_menu_item_has_no_state_badges` (scope al anchor `services_commercial_public`, assertNotIn badge/bg-blue-lt/bg-orange-lt + count == 1) | ✅ COMPLIANT |
| REQ-10 S1 | Badge padre visible con pendientes | `test_menu_dot_animated_shown_when_pending_actions` (badge `bg-red-lt` presente, `status-dot` ausente) | ✅ COMPLIANT |
| REQ-10 S2 | Sin pendientes, sin badge padre | `test_menu_dot_animated_hidden_without_pending_actions` (sin `bg-red-lt`, sin dot, item visible) | ✅ COMPLIANT |
| REQ-10 S3 | Badge padre suma correctamente | Ídem — mecanismo de suma (`client_pending_actions`) cubierto con fixture 1+1=2 | ✅ COMPLIANT |

#### customer-services-dashboard (REQ-04, REQ-05)

| Req | Escenario | Test | Resultado |
|---|---|---|---|
| REQ-04 S1 | Pending con QR ofrece factura y pago | `CommercialServicesListContextualActionsTests.test_pending_qr_offers_invoice_and_qr_payment` (URL `factura/{uuid}/pdf/?inline=1`, `ti-qrcode`, `home:payment`) | ✅ COMPLIANT |
| REQ-04 S2 | Pending sin facturas no muestra Ver factura | `test_pending_subscription_without_invoice_hides_invoice_button` (assertNotIn 'Ver factura', '/factura/', 'ti ti-receipt' con pending+qr sin invoices; assertIn 'Pagar con QR') | ✅ COMPLIANT |
| REQ-04 S3 | Pending transfer usa icono bancario | `test_pending_transfer_offers_invoice_without_qr` (URL factura + `ti-building-bank`) | ✅ COMPLIANT |
| REQ-04 S4 | Pending presencial usa icono tienda | `PaymentMethodIconFilterTests.test_presencial_maps_to_building_store` (mapeo unit) | ✅ COMPLIANT |
| REQ-04 S5 | Solicitado sin botones | `test_requested_shows_progress_badge_without_action_buttons` (badge "En proceso", ausencia de "Ver factura"/"Pagar con QR"/"Ver PDF"/`ti-send`) | ✅ COMPLIANT |
| REQ-05 S1 | Calendario precede al rango | `CommercialServicesListViewStateScopeTests.test_calendar_icon_precedes_date_range_in_dom` | ✅ COMPLIANT |
| REQ-05 S2 | Precio sin icono dollar | `test_subscription_no_dollar_icon_in_price` | ✅ COMPLIANT |
| REQ-05 S3 | Layout orden fechas-pago-precio | `test_metadata_layout_order_is_dates_payment_price` (índices DOM relativos fechas < pago < precio en scope metadata) | ✅ COMPLIANT |

#### home-public-services-layout (Requisito sin número)

| Req | Escenario | Test | Resultado |
|---|---|---|---|
| Requirement S1 | Card sin ribbon ni botones de estado | `ServiceReRequestUiTests.test_public_list_active_shows_state_neutral_card` + `test_public_list_state_neutral_regardless_of_subscription_state` + `test_pending_non_qr_public_catalog_is_state_neutral` | ✅ COMPLIANT |
| Requirement S2 | Card anónimo sin ribbon | `ServicesCommercialStaffButtonTests.test_anonymous_sees_login_cta_only_and_no_ribbon` | ✅ COMPLIANT |
| Requirement S3 | Precio sin icono dollar | `test_catalog_no_currency_dollar_icon` (`$200,00` sin `ti-currency-dollar`) | ✅ COMPLIANT |
| Requirement S4 | Sin bloque código | `test_catalog_shows_category_badge_and_code` (`assertNotIn('Código: C200', html)`) + `test_catalog_hides_code_label_when_service_has_no_code` | ✅ COMPLIANT |
| Requirement S5 | Badge categoría pronóstico con icono | `test_catalog_category_badge_has_cloud_icon` (`ti-cloud` + "Pronóstico") | ✅ COMPLIANT |
| Requirement S6 | Badge categoría agrometeo con icono | `test_catalog_category_badge_has_plant_icon` (`ti-plant` + "Agrometeorológico") | ✅ COMPLIANT |

**Compliance summary**: 21/21 escenarios COMPLIANT, 0 PARTIAL, 0 UNTESTED

### Correctness (Evidencia estática)

| Req | Estado | Evidencia |
|---|---|---|
| REQ-09 | ✅ Implementado | `menu-list.html:133-135` badge `bg-red-lt` en toggle padre (sin dot); `:156-161` badges `bg-blue-lt`/`bg-orange-lt` en "Mis Servicios"; `:143-147` "Servicios Comerciales" sin badges |
| REQ-10 | ✅ Implementado | `menu-list.html:134` patrón idéntico a Avisos `:58`; `status-dot` eliminado del template |
| REQ-04 | ✅ Implementado | `views.py:52-56` `latest_invoice` por suscripción; `commercial.html:66-73` botón condicional `{% if invoice %}` → `factura_download/<uuid>?inline=1`; `:38` filtro `payment_method_icon` |
| REQ-05 | ✅ Implementado | `commercial.html:31-45` orden DOM fechas → pago → precio; sin `ti-currency-dollar`; precio `format_cup` + período (`:43`) |
| home-public-services-layout | ✅ Implementado | `commercial_public.html:28-35` badge categoría con icono diferenciado (`ti-cloud`/`ti-plant`); `:39` precio `format_cup` sin dollar; sin bloque "Código:"; sin ribbons ni `user_subscriptions`/`now` |

### Coherence (Design)

| Decisión de diseño | ¿Seguida? | Notas |
|---|---|---|
| Filtro `payment_method_icon` en `utils_filters.py` (no if-chain en template) | ✅ Sí | `utils_filters.py:70-78`; `@register.filter(name='payment_method_icon')`; mapeo exacto qr/transfer/presencial/default |
| Helper en `get_context_data` con loop (no Subquery) | ✅ Sí | `views.py:52-56`; 1 query ligera por sub (`order_by('-issue_date').first()`) |
| `subscription.latest_invoice` como objeto (no uuid suelto) | ✅ Sí | `views.py:54`; template usa `{% with invoice=subscription.latest_invoice %}` |
| Layout metadata uniforme (fechas → pago → precio, spans directos de `.d-flex.flex-wrap.gap-2`) | ✅ Sí | `commercial.html:31-45` |
| Patrón badge Avisos `bg-red-lt ms-2` exacto | ✅ Sí | `menu-list.html:134` == `:58` |
| `history.back()` con guard `window.history.length>1` + href fallback | ✅ Sí | `400/403/404/500.html:22`; href `home:index` conservado |
| Badge categoría con icono diferenciado | ✅ Sí | `commercial_public.html:29-33` |
| Estrategia de tests del diseño | ✅ Sí | Tests 4.1-4.5 y nuevos según diseño; 3 tests de remediación ahora cubren REQ-09 S4, REQ-04 S2, REQ-05 S3 |

### TDD Compliance

| Check | Resultado | Detalles |
|---|---|---|
| TDD Evidence reported | ✅ | `apply-progress.md` declara "Mode: STRICT TDD" e incluye tabla "TDD Cycle Evidence" con 10 filas (tasks 1.1-5.3 + R1-R5) |
| All tasks have tests | ✅ | 23/23 tasks; archivos de test existen y pasan |
| RED confirmed (tests exist) | ✅ | `test_services_ui.py` — `PaymentMethodIconFilterTests` (5 unit), `ErrorPagesHistoryBackTests` (3), 5 métodos actualizados + 8+3 métodos nuevos |
| GREEN confirmed (tests pass) | ✅ | 548/548 en ejecución real (exit 0) |
| Triangulation | ✅ | 21/21 escenarios con test que aserta comportamiento; R1-R3 añaden triangulación específica (ausencia scoped, presencia vs ausencia, orden DOM inter-span) |
| Safety Net | ✅ | Apply-progress reporta safety net pre-remediación: 53 OK → 56 OK → 54/54 post-format |

**TDD Compliance**: 6/6 checks completos.

### Test Layer Distribution

| Capa | Tests | Archivos | Herramientas |
|---|---|---|---|
| Unit | 5 (`PaymentMethodIconFilterTests` — mapeo exacto del filtro, incl. default y None) | 1 | unittest Django |
| Integration | 49 (resto de `test_services_ui.py`: 54 totales − 5 unit) | 1 | Django test Client (render real con middleware + context processors) |
| E2E | 0 | — | no aplica (sin tooling E2E en el proyecto) |
| **Total (archivo del cambio)** | **54** | **1** | dentro de **548** (suite selectiva apps.home+apps.commercial+apps.core) |

### Changed File Coverage

Coverage tool no disponible (`coverage_tool: none`). Análisis cualitativo: los 54 tests renderizan las vistas/templates modificados con el stack real; los 10 archivos del cambio están ejercitados en runtime (menú, Mis Servicios, catálogo público, error pages, filtro, contexto de vista). No se reporta % de líneas.

### Assertion Quality

**Assertion quality**: ✅ All assertions verify real behavior — 0 tautologías, 0 ghost loops, 0 smoke tests, 0 aserciones tipo-only.

- `PaymentMethodIconFilterTests` (5 unit): valores exactos del mapeo con 5 inputs distintos (qr, transfer, presencial, unknown, None).
- Tests de integración: aserciones de contenido HTML real (clases CSS, URLs resueltas `factura/{uuid}/pdf/?inline=1`, textos, ausencias, orden DOM inter-span).
- R1 (REQ-09 S4): scope al anchor `services_commercial_public`, assertNotIn badge + count == 1 — triangula contra presencia en "Mis Servicios".
- R2 (REQ-04 S2): triple assertNotIn ('Ver factura', '/factura/', 'ti ti-receipt') + assertIn 'Pagar con QR' — cubre ausencia completa del botón.
- R3 (REQ-05 S3): índices DOM relativos (dates < payment < price) en scope metadata — orden inter-span verificado.

### Quality Metrics

**Linter (ruff)**: ✅ No errors — `ruff check apps/home/tests/test_services_ui.py` → "All checks passed!" (exit 0)
**Formatter (ruff format --check)**: ⚠️ 2 archivos con diff — `utils_filters.py:19` y `views.py:67/104` ya diferían antes del cambio (condición pre-existente del repo, no atribuible a este change). `test_services_ui.py` ya formateado.
**Type Checker**: ➖ No disponible (`config.yaml` `type_checker: none`).
**Template linter (djlint)**: ✅ `--lint` 0 errores, `--reformat --check` 0 archivos a actualizar (7/7 templates del cambio).

### Issues Found

**CRITICAL**: None

**WARNING**:

1. **ruff-format --check sugiere reformatear `utils_filters.py:19` y `views.py:67/104`** — diffs pre-existentes del repo, NO atribuibles a este cambio. El verify anterior los excluyó correctamente.

**SUGGESTION**:

1. **Guard `hasattr(sub, 'invoices')` inalcanzable** (`views.py:53-56`): el queryset de `ServiceSubscription` siempre expone el reverse manager `invoices`; la rama else nunca se ejecuta (defensivo, inofensivo — puede simplificarse).
2. **Cobertura de integración para presencial (REQ-04 S4)**: hoy el icono `ti-building-store` solo está cubierto a nivel unit del filtro; un test de render (pending+presencial+invoice → `ti-building-store` + URL factura) daría cobertura completa del escenario a nivel card.
3. **Test dedicado para el total suma (REQ-10 S3)** con fixture 3 requested + 2 pending → "5": hoy el mecanismo está cubierto con 1+1=2; el valor exacto "5" del escenario no se aserta.

### Verdict

**PASS**

Los 4 hallazgos CRITICAL del verify anterior están RESUELTOS con evidencia real: (1) REQ-09 S4 — test `test_services_commercial_menu_item_has_no_state_badges` aserta ausencia de badges en "Servicios Comerciales" con scope al anchor real; (2) REQ-04 S2 — test `test_pending_subscription_without_invoice_hides_invoice_button` aserta triple ausencia de "Ver factura" con fixture pending+qr sin invoices; (3) REQ-05 S3 — test `test_metadata_layout_order_is_dates_payment_price` aserta orden DOM inter-span fechas < pago < precio; (4) TDD evidence — `apply-progress.md` reporta modo STRICT TDD y tabla TDD Cycle Evidence completa. Suite 548/548 verde (exit 0), `manage.py check` sin issues, djlint 0 errores, ruff check limpio en archivo del cambio. 21/21 escenarios COMPLIANT. E501 previo remediado.

### Next Recommended

**archive**: todos los requisitos, escenarios y tasks están completos. La fase archive debe promover los specs y archivar el cambio.
