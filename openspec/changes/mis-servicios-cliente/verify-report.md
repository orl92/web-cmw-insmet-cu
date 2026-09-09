```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:9a33e4e05408b0888d9385cb90f92f49d54c1977e4f07d726b5869f63cd79065
verdict: fail
blockers: 11
critical_findings: 11
requirements: 4/13
scenarios: 8/23
test_command: source .venv/bin/activate && python manage.py test
test_exit_code: 0
test_output_hash: sha256:343af41dc66bae986e5c1b2e9e1d8bc206924c3bd6af81cdf60f3d020ad9e87b
build_command: source .venv/bin/activate && python manage.py check
build_exit_code: 0
build_output_hash: sha256:1e3e63f221bde88816c4a4ef7367691607b20cc1d194028a02ec9ae0586cf9b1
```

## Verification Report

**Change**: mis-servicios-cliente
**Version**: spec delta v1 (`openspec/changes/mis-servicios-cliente/specs/mis-servicios-cliente/spec.md`)
**Mode**: Strict TDD (activado por el orquestador; módulo `strict-tdd-verify.md` cargado)
**Rama**: `feat/mis-servicios-cliente-1` (base `main@1053af5`, HEAD `a8ab4a4`)

### Completeness

| Métrica | Valor |
|---|---|
| Tasks total | 24 |
| Tasks completas | 24 |
| Tasks incompletas | 0 |
| Requisitos (spec delta) | 13 (REQ-01..REQ-11 + 2 `### Requirement:` de capabilities delta) |
| Escenarios | 23 |
| Escenarios con test que pasa (COMPLIANT) | 8 |
| Escenarios parciales (PARTIAL) | 4 |
| Escenarios sin test (UNTESTED) | 11 |

### Build & Tests Execution

**Build (Django check)**: ✅ Passed — `python manage.py check` → "System check identified no issues (0 silenced)."

**Tests**: ✅ 672 passed / ❌ 0 failed / 0 skipped — `python manage.py test` → `Ran 672 tests in 286.279s` → `OK` (los `ERROR` del log son ruido esperado de tests de monitoreo Huey/simulación de fallos).

**djlint**: ✅ `djlint . --lint` → "Linted 160 files, found 0 errors." (exit 0)

| Evidencia | Valor |
|---|---|
| test_command | `python manage.py test` |
| test_exit_code | 0 |
| test_output_hash | `343af41dc66bae986e5c1b2e9e1d8bc206924c3bd6af81cdf60f3d020ad9e87b` |
| build_command | `python manage.py check` |
| build_exit_code | 0 |
| build_output_hash | `1e3e63f221bde88816c4a4ef7367691607b20cc1d194028a02ec9ae0586cf9b1` |
| djlint_exit_code | 0 |
| djlint_output_hash | `384782162ce1b50f772d5a3735f5b0ace6a487e297ca3d4771d48d7db3074660` |

**Coverage**: ➖ No hay tool de coverage configurada en el proyecto (no es fallo; se reporta análisis por archivos vía inspección).

### Spec Compliance Matrix

| Req | Escenario | Test | Resultado |
|---|---|---|---|
| REQ-01 | Precio con miles | `apps/core/tests/test_templatetags.py > FormatCupFilterTest > test_decimal_with_thousands_separator` | ✅ COMPLIANT |
| REQ-01 | Precio pequeño sin miles | `test_small_decimal_uses_comma_for_decimals` + `test_commercial_row_keeps_price_and_subscription_count` (`$45,50`) | ✅ COMPLIANT |
| REQ-01 | Composición con período | `apps/home/tests/test_services_ui.py > ServiceReRequestUiTests > test_public_list_active_shows_state_neutral_card` (`$20,00` + render CUP/período) | ✅ COMPLIANT |
| REQ-02 | Todos los estados visibles | `CommercialServicesListViewStateScopeTests > test_lists_all_subscription_states_in_priority_order` | ✅ COMPLIANT |
| REQ-02 | Orden por prioridad de acción | mismo test (`positions == sorted(positions)`) | ✅ COMPLIANT |
| REQ-03 | Ribbon correcto por estado | (ninguno — no se aserta `bg-green`/texto "activo") | ❌ UNTESTED |
| REQ-03 | Expired muestra ribbon rojo | (ninguno — no se aserta `bg-red`/"expirado") | ❌ UNTESTED |
| REQ-04 | Pending con QR ofrece factura y pago | (ninguno — no se aserta "Ver factura"/"Pagar con QR"/URLs `commercial:factura_list`/`home:payment`) | ❌ UNTESTED |
| REQ-04 | Solicitado sin botones | (ninguno — no se aserta badge "En proceso") | ❌ UNTESTED |
| REQ-05 | Calendario precede al rango | (ninguno — no hay test de orden DOM del icono `ti-calendar-month`) | ❌ UNTESTED |
| REQ-06 | Cliente con sub activa ve card limpio | `test_public_list_active_shows_state_neutral_card` / `test_public_list_state_neutral_regardless_of_subscription_state` / `test_pending_non_qr_public_catalog_is_state_neutral` | ✅ COMPLIANT |
| REQ-06 | Anónimo ve botón de login | (ninguno — ningún test aserta "Iniciar sesión"/`ti-login` en el catálogo anónimo) | ❌ UNTESTED |
| REQ-07 | Iconos presentes en detail | (ninguno — ningún test aserta `ti-send`/`ti-x`/`ti-eye`) | ❌ UNTESTED |
| REQ-08 | Admin muestra $45,50 | `apps/commercial/tests/test_views.py > test_commercial_row_keeps_price_and_subscription_count` | ✅ COMPLIANT |
| REQ-09 | Badge suma requested + pending | `apps/core/tests/test_context_processors.py > test_client_pending_actions_sums_requested_and_pending` (variable = 2) — sin aserción del badge "2" renderizado en menú | ⚠️ PARTIAL |
| REQ-09 | Menú visible con solo expirada | `MisServiciosMenuItemTests > test_menu_shows_mis_servicios_with_expired_subscription` — visibilidad OK; badge oculto a 0 no asertado | ⚠️ PARTIAL |
| REQ-10 | Dot visible con pendientes | (ninguno — ningún test aserta `status-dot status-dot-animated`) | ❌ UNTESTED |
| REQ-10 | Sin pendientes, sin dot | (ninguno) | ❌ UNTESTED |
| REQ-11 | Submit unificado con paid activa | `ServiceReRequestUiTests > test_active_paid_renders_form_and_cta` ("Solicitar" + "activa hasta") + `test_in_flight_*` (bloqueo) | ✅ COMPLIANT |
| home-public-services-layout | Card sin ribbon ni botones de estado | tests state-neutral (ausencia de texto "Activo"/"Solicitado"/"Solicitar de nuevo" + "Solicitar" único) — sin aserción de clases `bg-*` | ⚠️ PARTIAL |
| home-public-services-layout | Card anónimo sin ribbon | (ninguno — ver REQ-06 anónimo) | ❌ UNTESTED |
| commercial-service-categories | Badge y código visibles | badge "Pronóstico" asertado; `Código: C200` sin test (ninguna fixture con `code` en catálogo público) | ⚠️ PARTIAL |
| commercial-service-categories | Sin código no se muestra etiqueta | (ninguno — no se aserta ausencia de "Código:") | ❌ UNTESTED |

**Resumen de cumplimiento**: 8/23 escenarios COMPLIANT, 4 PARTIAL, 11 UNTESTED.

### Correctness (Evidencia estática)

| Req | Estado | Evidencia |
|---|---|---|
| REQ-01 | ✅ Implementado | `apps/core/templatetags/utils_filters.py:14-19` — `format_cup` (miles `.`, decimal `,`, None → `$0,00`); composición en `commercial.html:45`, `commercial_public.html:34`, `service_detail.html:36,40`, `admin list.html:20` |
| REQ-02 | ✅ Implementado | `views.py:26-44` — `filter(customer=customer, record_active=True)` sin filtro de estado + Case/When requested=0→expired=3, luego `-start_date` |
| REQ-03 | ✅ Implementado | `views.py:19-24` (`STATUS_RIBBONS`) + `views.py:51` inyección; `commercial.html:21` usa `status_ribbon\|get_item:subscription.status_display`; keys coinciden con `models.py:232-241` (`status_display`) |
| REQ-04 | ✅ Implementado | `commercial.html:51-86` — activo→modal PDF (`is_active` = paid + vigente, `models.py:229-230`); pending+qr→factura+QR; pending otro→factura; requested→"En proceso" sin botones; else→"Solicitar" |
| REQ-05 | ✅ Implementado | `commercial.html:31-47` — icono `ti-calendar-month` antes del rango; precio `format_cup` + período; método de pago |
| REQ-06 | ✅ Implementado | `commercial_public.html:28-69` — badge categoría, summary, precio, código, botón único; sin ribbons; `views.py:66-71` sin `user_subscriptions`/`now` |
| REQ-07 | ✅ Implementado | `commercial_public.html:67` (`ti-login`), `commercial.html:61,71,76,84` (`ti-file-type-pdf`, `ti-receipt`, `ti-qrcode`, `ti-send`), `service_detail.html:145,160,167` (`ti-eye`, `ti-send`, `ti-x`) |
| REQ-08 | ✅ Implementado | `apps/commercial/templates/pages/commercial/service/list.html:20` — `format_cup` reemplaza `floatformat:2` |
| REQ-09 | ✅ Implementado | `context_processors.py:76-78` — suma en path normal tras ambos queries; `menu-list.html:159` condición 4 contadores; `menu-list.html:169-171` badge `client_pending_actions` con `{% if > 0 %}` |
| REQ-10 | ✅ Implementado | `context_processors.py:76-78` + `menu-list.html:133-135` dot `status-dot status-dot-animated bg-red` con `{% if client_pending_actions > 0 %}` en el toggle Servicios |
| REQ-11 | ✅ Implementado | `service_detail.html:159-161` submit "Solicitar" + `ti ti-send`; `:165-168,170-173` Cancelar `ti-x`; alerta de vigencia `:67-73`; bloqueo in-flight `:55-66` |

### Coherence (Design)

| Decisión de diseño | ¿Seguida? | Notas |
|---|---|---|
| Filtro `format_cup` en `utils_filters.py` (no tocar modelo) | ✅ Sí | Formato manual, sin dependencia de locale de entorno |
| Queryset Mis Servicios sin filtro + Case/When + `-start_date` | ✅ Sí | `views.py:31-44`; `record_active=True` extra (soft delete, acorde a convención del proyecto) |
| `STATUS_RIBBONS` dict inyectado + `get_item` | ✅ Sí | Exacto a diseño |
| Acciones por estado en template (sin helper extra) | ✅ Sí | Igual a la tabla del diseño y specs |
| Catálogo público sin `user_subscriptions`/`now` | ✅ Sí | `views.py:66-71` |
| Fix `client_pending_actions` en path normal | ✅ Sí | `context_processors.py:76-78` |
| Menú con ≥1 suscripción + badge pending | ✅ Sí | `menu-list.html:159,169-171` — ver SUGGESTION sobre precedencia `and`/`or` |
| RISK-1: admin usa format_cup + aserción `$45,50` | ✅ Sí | `list.html:20`, `test_views.py` (`assertIn('$45,50', html)`) |
| Íconos (qrcode/login/eye/send/x/receipt/file-type-pdf) | ✅ Sí | Los 7 presentes en los templates correctos |

### TDD Compliance

| Check | Resultado | Detalles |
|---|---|---|
| TDD evidence reported | ⚠️ Parcial | apply-progress en Engram `sdd/mis-servicios-cliente/apply-progress` (#256): tabla TDD Cycle solo de Phase 4 (4.1-4.10); el upsert acumulado no conserva las tablas RED/GREEN de slices 1-3 (Revisions: 3) |
| All tasks have tests | ✅ | 24/24 tasks; 3 archivos de test del cambio existen y pasan |
| RED confirmed (tests exist) | ✅ | `test_services_ui.py`, `test_context_processors.py`, `test_templatetags.py` existen y corren |
| GREEN confirmed (tests pass) | ✅ | 672/672 en ejecución independiente |
| Triangulation | ⚠️ | 8 escenarios sin test; 4 parciales; REQ-02 cubre 2 escenarios con 1 test (con aserciones de orden, adecuado) |
| Safety Net | ⚠️ | Sin evidencia retenida para slices 1-3 (tablas overwriteadas en el upsert) |

**TDD Compliance**: 3/6 checks completos, 3 parciales — el problema no es red/green (todo verde) sino cobertura de aserciones de escenarios especificados.

### Test Layer Distribution

| Capa | Tests | Archivos | Herramientas |
|---|---|---|---|
| Unit | 10 nuevos (7 `format_cup` + filtro template + 2 context processor) | `test_templatetags.py`, `test_context_processors.py` | unittest Django |
| Integration | 11 nuevos/ampliados (estados, orden, menú, catálogo neutral, detail) | `test_services_ui.py` | test Client Django |
| E2E | 0 | — | no aplica (sin tooling E2E en el proyecto) |
| **Total** | **~21** (cambio) dentro de **672** (suite) | 3 | |

### Changed File Coverage

➖ No hay tool de coverage configurada en el proyecto. Información cualitativa: los 3 archivos de tests del cambio ejercitan todas las vistas/templates modificados en runtime (render real con middleware y context processors); el hueco no es de ejecución sino de aserciones (ver Assertion Quality / matriz).

### Assertion Quality

| Archivo | Línea | Aserción | Issue | Severidad |
|---|---|---|---|---|
| `apps/home/tests/test_services_ui.py` | 233-245 | títulos + orden por prioridad | Ninguno — aserciones de valor real y orden | OK |
| `apps/core/tests/test_context_processors.py` | 57-71 | counts = 1/1/2 y active/expired | Ninguno — ejercita `menu_notifications` de verdad | OK |
| `apps/core/tests/test_templatetags.py` | 10-35 | valores exactos de formato | Ninguno — 8 casos con valores distintos (1234.56, 45.50, 0, None, etc.) | OK |

**Assertion quality**: ✅ All assertions verify real behavior — 0 CRITICAL, 0 WARNING. Sin tautologías, sin ghost loops, sin smoke tests; el único patrón a vigilar es ausencia de aserciones para escenarios de UI (por eso UNTESTED, no por aserciones triviales).

### Issues Found

**CRITICAL** (11 escenarios especificados sin test que aserte su comportamiento — la implementación es correcta por inspección, pero la regla de verificación exige cobertura runtime):

1. **REQ-03 Ribbon dinámico** — 2 escenarios UNTESTED: ningún test aserta `bg-green`/texto "activo" ni `bg-red`/"expirado" en Mis Servicios. Código: `commercial.html:21`, dict `views.py:19-24`. Diseño pedía "Integration: verificar clase CSS correcta por estado" (design.md:168).
2. **REQ-04 Acciones contextuales** — 2 escenarios UNTESTED: ningún test aserta botones "Ver factura"/"Pagar con QR" + URLs `commercial:factura_list`/`home:payment` (pending+qr), ni badge "En proceso" sin botones (requested). Código: `commercial.html:68-86`. Diseño pedía "verificar botones/URLs por estado" (design.md:169). (La fila "activo → Ver PDF modal" sí tiene cobertura preexistente: `test_ver_pdf_trigger_keeps_data_pdf_url_and_title`.)
3. **REQ-05 Metadatos normalizados** — 1 escenario UNTESTED: sin test del orden DOM calendario→rango (`commercial.html:33-34`).
4. **REQ-06 escenario anónimo** — 1 escenario UNTESTED: ningún test aserta "Iniciar sesión" + `ti-login` en catálogo anónimo (`commercial_public.html:65-68`). `test_anonymous_sees_no_management_buttons` solo aserta ausencia de botones staff.
5. **REQ-07 Iconos** — 1 escenario UNTESTED: ningún test aserta `ti ti-send`/`ti ti-x`/`ti ti-eye` en detail.
6. **REQ-10 Dot animado** — 2 escenarios UNTESTED: ningún test aserta presencia/ausencia de `status-dot status-dot-animated` en el menú (depende del render del toggle Servicios, `menu-list.html:133-135`); solo hay unit del contador.
7. **Delta home-public-services-layout, escenario anónimo** — sin test del control único "Iniciar sesión" sin ribbon.
8. **Delta commercial-service-categories** — escenario "Badge y código visibles" PARTIAL (falta fixture con `code` en catálogo público; ningún test aserta "Código: C200") y escenario "Sin código no se muestra etiqueta" UNTESTED.

**WARNING**:

1. **Evidencia TDD incompleta para slices 1-3**: el apply-progress (upsert en Engram, topic `sdd/mis-servicios-cliente/apply-progress`) solo conserva la tabla TDD Cycle de Phase 4. Las tablas RED/GREEN/REFACTOR de tasks 1.1-3.5 se perdieron en las 3 revisiones del upsert; la evidencia de "safety net" previa a modificación no es auditable.
2. **Design deviation menor — empty-state**: `commercial.html:103` dice "No tienes servicios contratados en este momento." (no estaba en el literal de la task; el propio apply lo anotó como desviación conocida). No rompe ninguna REQ — es texto de vacío.

**SUGGESTION**:

1. **Precedencia `and`/`or` en `menu-list.html:159`**: `… and client_active_count > 0 or client_expired_count > 0 or …` se evalúa como `(A and B and C) or D or E or F`. Funciona en todos los escenarios actuales (los contadores solo existen para clientes autenticados), pero es frágil: agrupar explícitamente con el guard de auth, p. ej. `{% if user.is_authenticated and user.commercial_customer and (client_active_count|add:client_expired_count|add:client_requested_count|add:client_pending_count) > 0 %}`.
2. **`default_if_none:'—'` muerto en `commercial_public.html:34`**: `format_cup(None)` ya retorna `$0,00`; el filtro nunca devuelve None. Limpiable (mantenido por literalidad de la task, según apply).
3. ***Index* estricto en `menu-list.html:159`**: `client_active_count`/`client_expired_count`/etc. solo se definen para clientes con `commercial_customer`; para staff sin customer la condición depende de variables inexistentes (resuelven a falsy en templates Django) — recomendar definir los 4 contadores a 0 en el branch staff para hacer la condición robusta.
4. **Test del contador con `RequestFactory`** (`test_context_processors.py`): correcto y suficiente, pero el render del badge/dot del menú (REQ-09/10) debería asertarse a nivel integración con el test client (mismo patrón que `MisServiciosMenuItemTests`).

### Verdict

**FAIL**

La implementación cumple proposal, design y spec por inspección estática (13/13 REQs implementados, 24/24 tasks, suite 672/672 verde, check y djlint limpios), pero **11 de 23 escenarios especificados carecen de test que aserte su comportamiento en runtime** (ribbons, acciones contextuales, orden de metadatos, iconos, dot del menú, control anónimo y código de catálogo). Bajo la regla del skill —"un escenario de spec es compliant solo si un test que lo cubre pasa en runtime"— estos escenarios son CRITICAL `UNTESTED` y bloquean la certificación del cambio. Es un problema de cobertura de tests (corrección pequeña y acotada), no de implementación.

### Next Recommended

**Corrección** (no archive): añadir tests de integración en `apps/home/tests/test_services_ui.py` (+1 en `apps/core` o reutilizar `test_services_ui.py` para menú) que aserten: (a) ribbons `bg-green`/`bg-orange`/`bg-blue`/`bg-red` + texto de estado por cada uno de los 4 estados en Mis Servicios, (b) pending+qr → "Ver factura" (`commercial:factura_list`) + "Pagar con QR" (`home:payment`), requested → "En proceso" sin botones, (c) orden DOM calendario → rango, (d) iconos `ti ti-send`/`ti ti-x` en detail, (e) menú: badge "2" (requested+pending), dot `status-dot-animated` presente/ausente, (f) catálogo anónimo → "Iniciar sesión" + `ti-login` único, (g) catálogo con `code` → "Código: C200"/sin code sin etiqueta. Re-ejecutar `python manage.py test` completo y re-verificar.

### Risks

- Ninguno de implementación: sin migraciones, sin mutación de datos, cambios de display/lectura (plan de reversión trivial: revert de templates/views/context processor/filtro).
- Riesgo de proceso: la evidencia TDD de slices 1-3 no es auditable por el upsert del apply-progress (WARNING arriba).

## Key Learnings

1. Un escenario de spec solo es compliant si existe un test que aserte su comportamiento y pase en runtime; el render sin aserción no cuenta como cobertura.
2. La suite completa de 672 tests tardó 286s y pasó íntegra, incluyendo el render de los 4 estados de Mis Servicios con el stack real (middleware, context processors, templates).
3. El patrón `status_ribbon|get_item:subscription.status_display` alinea exactamente los strings del `status_display` del modelo con el dict de la vista, eliminando el ribbon hardcodeado.
4. El upsert del apply-progress en Engram sobrescribe las tablas TDD de slices previos; la evidencia RED/GREEN histórica de slices 1-3 no quedó auditable.
5. `format_cup` implementa el formateo manualmente (sin `locale.setlocale`), por lo que el formato `$1.234,56` es determinista en entornos de test y producción.

## Corrección aplicada (remediación de verify)

Revisión de evidencias remediada: `sha256:9a33e4e05408b0888d9385cb90f92f49d54c1977e4f07d726b5869f63cd79065` (FAIL — 11 escenarios UNTESTED).

**Alcance**: solo tests de integración en `apps/home/tests/test_services_ui.py` (+ actualización de este reporte). Sin cambios en vistas, templates, context processors ni filtros.

### Escenarios cubiertos (11/11 UNTESTED con test verde)

| Escenario (verify-report) | Test añadido | Aserciones clave |
|---|---|---|
| REQ-03 Ribbon correcto por estado | `CommercialServicesListViewStateScopeTests.test_ribbon_class_and_label_per_subscription_state` | dict `status_ribbon` en context (`activo→bg-green`, `pendiente de pago→bg-orange`, `solicitado→bg-blue`, `expirado→bg-red`); HTML `ribbon-bookmark <clase>">activo` etc.; 1 ribbon por card |
| REQ-03 Expired muestra ribbon rojo | mismo test | `ribbon-bookmark bg-red">expirado` |
| REQ-04 Pending con QR ofrece factura y pago | `CommercialServicesListContextualActionsTests.test_pending_qr_offers_invoice_and_qr_payment` | "Ver factura" + href `commercial:factura_list`; "Pagar con QR" + href `home:payment` |
| REQ-04 Solicitado sin botones | `CommercialServicesListContextualActionsTests.test_requested_shows_progress_badge_without_action_buttons` | badge "En proceso" presente; ausencia de "Ver factura"/"Pagar con QR"/"Ver PDF"/`ti-send` |
| REQ-05 Calendario precede al rango | `CommercialServicesListViewStateScopeTests.test_calendar_icon_precedes_date_range_in_dom` | `html.index('ti-calendar-month') < html.index(fecha-inicio d/m/Y)` |
| REQ-06 Anónimo ve botón de login | `ServicesCommercialStaffButtonTests.test_anonymous_sees_login_cta_only_and_no_ribbon` (extiende y renombra el test anónimo previo) | marcado `<i class="icon ti ti-login"></i> Iniciar sesión`; sin `ti-send`, sin botones staff |
| REQ-07 Iconos presentes en detail | `ServiceReRequestUiTests.test_detail_renders_action_icons` | `ti-send` (submit Solicitar), `ti-eye` (Ver relacionado), `ti-x` (Cancelar) |
| REQ-10 Dot visible con pendientes | `MisServiciosMenuItemTests.test_menu_dot_animated_shown_when_pending_actions` | `status-dot status-dot-animated bg-red` + badge `bg-orange ms-2">2` (cierra el PARTIAL de REQ-09 badge "2") |
| REQ-10 Sin pendientes, sin dot | `MisServiciosMenuItemTests.test_menu_dot_animated_hidden_without_pending_actions` | sin dot ni badge con solo sub `paid`; item Mis Servicios sigue visible (cierra el PARTIAL de REQ-09 badge oculto a 0) |
| Delta home-public-services-layout: card anónimo sin ribbon | consolidado en el test anónimo de REQ-06 | `ribbon-bookmark` ausente; control único "Iniciar sesión" |
| Delta commercial-service-categories: sin código sin etiqueta | `CommercialCatalogCodeAndCategoryUITests.test_catalog_hides_code_label_when_service_has_no_code` | ausencia de "Código:" en el catálogo |
| Delta commercial-service-categories: badge y código visibles (era PARTIAL) | `CommercialCatalogCodeAndCategoryUITests.test_catalog_shows_category_badge_and_code` | badge "Agrometeorológico" + "Código: C200" |

Triangulación adicional de REQ-04: `test_pending_transfer_offers_invoice_without_qr` (pending no-QR → solo "Ver factura", sin "Pagar con QR").

### Evidencia de ejecución (remediación)

- `python manage.py test apps.home.tests.test_services_ui` → **37 tests OK** (baseline 27 + 10 nuevos)
- `python manage.py test apps.home apps.core` → **347 tests OK**
- `python manage.py check` → sin issues
- `ruff check` y `ruff format --check` sobre el archivo de tests → limpio
- Rollback: revert del commit de tests + borrado de esta sección del reporte (sin cambios de producción, reversión trivial)

### Estado de cumplimiento tras la remediación

| Métrica | Antes | Después |
|---|---|---|
| Escenarios COMPLIANT | 8/23 | 19/23 |
| Escenarios PARTIAL | 4/23 | 2/23 (aserciones de clases `bg-*` en el card state-neutral logueado — fuera del alcance de los 11 UNTESTED) |
| Escenarios UNTESTED | 11/23 | 0/23 |