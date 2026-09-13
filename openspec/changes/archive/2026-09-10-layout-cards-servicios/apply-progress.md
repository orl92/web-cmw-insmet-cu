# Apply Progress: Layout Cards Servicios

**Store**: openspec — `openspec/changes/layout-cards-servicios/`
**Modo**: Strict TDD (config `testing.strict_tdd: true`; runner Django unittest)
**Delivery**: single PR (auto-chain cacheado; forecast 150-180 líneas, riesgo Low, `Decision needed: No`)
**Fecha**: 2026-09-10

## Resumen

Template-only + tests (0 backend). Cards del catálogo público y de Mis Servicios alineados con el patrón de metadata de `service_detail.html`: líneas `<div class="mb-2">` independientes con icono `me-1` y precio destacado `display-6 fw-bold text-primary`. Pin vertical unificado vía wrapper `d-flex flex-column flex-grow-1 text-secondary mb-3` (design D1/D3). Baseline ROJO resuelto: `ti-calendar-month` corregido en `commercial.html` (L33).

## Tasks completadas

Todas las tareas de `tasks.md` (1.1, 2.1, 2.2, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2) marcadas `[x]`.

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 Catálogo template | `apps/home/tests/test_services_ui.py` | Integration (render vía view) | ✅ 54 run (2 known RED) | ✅ Written (3.2/3.3/3.4) | ✅ 61/61 | ✅ 3 casos: cloud / plant / orden categ→período→precio | ✅ djlint 0 errors |
| 2.1 Mis Servicios template | `apps/home/tests/test_services_ui.py` | Integration | ✅ 54 run (2 known RED) | ✅ Written (3.1/4.1-4.5) | ✅ 61/61 | ✅ 5 casos: strong / presencial / sin pago / PUBLIC / sin sufijo | ✅ djlint 0 errors |
| 2.2 grep `mt-auto` = 0 | verificación estructural | N/A | N/A | N/A | ✅ 0 ocurrencias | ➖ Single (única salida) | ➖ None |
| 3.1 Orden metadata fechas→pago→categoría→período→precio | `test_services_ui.py` | Integration | ✅ | ✅ RED (11 fallos en fase RED) | ✅ | ✅ (baseline 3.1 + 4.5 precios) | ✅ |
| 3.2 Iconos catálogo `me-1` antes de "Categoría:" | `test_services_ui.py` | Integration | ✅ | ✅ RED | ✅ | ✅ 2 categorías (cloud/plant) | ✅ |
| 3.3 Nuevo: orden DOM catálogo sin `flex-wrap gap-2` | `test_services_ui.py` | Integration | ✅ | ✅ RED | ✅ | ➖ Single (1 escenario spec) | ✅ |
| 3.4 Nuevo: precio `display-6` + `CUP/<período>` | `test_services_ui.py` | Integration | ✅ | ✅ RED | ✅ | ✅ agrometeo=`CUP/mes` | ✅ |
| 4.1 Nuevo: líneas categoría/período con `<strong>` | `test_services_ui.py` | Integration | ✅ | ✅ RED | ✅ | ➖ Single | ✅ |
| 4.2 Nuevo: icono pago presencial `ti-building-store` | `test_services_ui.py` | Integration | ✅ | ✅ RED | ✅ | ✅ (qr/transfer ya cubiertos por baseline) | ✅ |
| 4.3 Nuevo: sin `payment_method` omite línea | `test_services_ui.py` | Integration | ✅ | ✅ RED | ✅ | ✅ path distinto (ausencia vs presencia) | ✅ |
| 4.4 Nuevo: precio solo `commercial` | `test_services_ui.py` | Integration | ✅ | ✅ RED | ✅ | ✅ public vs commercial (caso opuesto en 3.1/4.5) | ✅ |
| 4.5 Nuevo: precio solo monto sin `CUP/` | `test_services_ui.py` | Integration | ✅ | ✅ RED | ✅ | ✅ (duplicación de período prohibida) | ✅ |
| 5.1 Verificación | `python manage.py check` + `apps.home --parallel` | N/A | — | — | ✅ 189/189 + check 0 issues | — | — |
| 5.2 djlint | ambos templates | N/A | — | — | ✅ `--reformat --check` 0 files + `--lint` 0 errors | — | — |

## Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `python manage.py test apps.home.tests.test_services_ui -v 1` → **Ran 61 tests, OK** (54 previos + 7 nuevos; 2 baseline RED ahora verdes) |
| Runtime harness command/scenario and exact result | `python manage.py check` → 0 issues; `python manage.py test apps.home --parallel` → **Ran 189 tests, OK** |
| Rollback boundary | `apps/home/templates/pages/home/services/commercial_public.html`, `commercial.html`, `apps/home/tests/test_services_ui.py` — revert de git restaura los 3 sin afectar los demás archivos modificados del working tree (pulido-ui-servicios sin commitear, ajeno a este cambio) |

## Archivos cambiados

| Archivo | Acción | Qué se hizo |
|---|---|---|
| `apps/home/templates/pages/home/services/commercial_public.html` | Modificado | L30-41 → wrapper `d-flex flex-column flex-grow-1 text-secondary mb-3` con 3 líneas `mb-2`: Categoría (icono `ti-cloud`/`ti-plant` me-1 + strong), Período (`ti-calendar-event`), Precio `display-6 fw-bold text-primary` + `<small>CUP/<período></small>`. Acciones intactas (`mt-auto` redundante D1 conservado) |
| `apps/home/templates/pages/home/services/commercial.html` | Modificado | L31-45 → wrapper con 4-5 líneas `mb-2`: Fechas `ti-calendar-month` (corrige baseline), Pago condicional `payment_method_icon`, Categoría `ti-tag`, Período `ti-calendar-event`, Precio solo monto si `commercial`. `mt-auto` = 0 (grep). Acciones intactas |
| `apps/home/tests/test_services_ui.py` | Modificado | 3.1 re-escopado al nuevo wrapper + orden de 5 líneas; 3.2 iconos `me-1` antes de "Categoría:" en su línea `mb-2`; nuevos 3.3, 3.4, 4.1-4.5; `_make_sub` acepta `payment_method` |

## Desviaciones del design

1. **`me-1` en iconos de fechas y pago (Mis Servicios)**: el bloque exacto entregado por el orquestador omitía `me-1` en esas dos líneas; tasks.md 2.1 y ambas specs exigen "icono `me-1` ANTES del texto". Se añadió `me-1` (superset trivial, sin impacto en tests ni layout).
2. Sin otras desviaciones — orden DOM, wrapper D1/D3, precio `display-6` D2, y `mt-auto` de acciones del catálogo (D1 redundante) tal como el design.

## Issues encontrados

- Quirk preexistente (no tocado, fuera de scope): en el catálogo, `default_if_none:'—'` nunca activa su fallback porque `format_cup(None)` devuelve `'$0,00'` (falsy → `'$0,00'`), no `None`.
- QA visual de `display-6` a 360px pendiente (pregunta abierta D2 del design): la clase es fluid en Tabler; si desborda, escalar a revisión de specs, no cambiar la clase en silencio.
- El working tree contiene cambios sin commitear de `pulido-ui-servicios` (archivado hoy) en archivos ajenos (`utils_filters.py`, `views.py`, `menu-list.html`, error templates, `openspec/specs/`). NO fueron tocados.

## Notas de ejecución

- Safety Net: 54 tests corriendo, exactamente los 2 RED documentados en design.md (baseline intencional, targets de este cambio). Ningún fallo inesperado.
- Fase RED: 11 fallos (3 failures + 8 errors) confirmados contra los templates viejos antes de implementar.
- Sin migraciones ni datos (solo templates + tests). Sin commits (decide el orquestador).