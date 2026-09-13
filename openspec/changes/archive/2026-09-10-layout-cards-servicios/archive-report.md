# Archive Report: layout-cards-servicios

**Change**: layout-cards-servicios
**Archived**: 2026-09-10 → `openspec/changes/archive/2026-09-10-layout-cards-servicios/`
**Store**: openspec
**Fecha de cierre**: 2026-09-10

## Estado final (al cierre)

Cambio template-only (2 templates + tests, 0 backend) que alinea los cards del catálogo público y de Mis Servicios con el patrón de metadata de `service_detail.html` (líneas `<div class="mb-2">` independientes con icono `me-1`, precio destacado `display-6 fw-bold text-primary`, pin vertical vía wrapper `d-flex flex-column flex-grow-1 text-secondary mb-3` — design D1). Baseline rojo resuelto: `ti-calendar-month` corregido en `commercial.html`.

| Métrica | Valor al cierre | Fuente |
|---|---|---|
| Tasks | 14/14 completas | `tasks.md` (persistido, sin checkboxes pendientes) + `sdd-status` pre-archive `taskProgress.allComplete: true` |
| Verdict verify | PASS — 0 blockers, 0 critical | `verify-report.md` |
| Escenarios | 16/16 COMPLIANT | `verify-report.md` |
| Tests enfocados | 61 OK (exit 0) | `verify-report.md` (snapshot de verificación) |
| Suite `apps.home --parallel` | 189 OK (exit 0) | `verify-report.md` (snapshot de verificación) |
| Django check | 0 issues | `verify-report.md` |
| djlint | 0 errores | `verify-report.md` |
| ruff | **Limpio al cierre** | Verificación en el árbol de trabajo al archivar: `ruff check apps/home/tests/test_services_ui.py` → "All checks passed!" |

## Lecturas (traceability)

Artifacts leídos (path store):

- `openspec/changes/layout-cards-servicios/proposal.md`
- `openspec/changes/layout-cards-servicios/specs/categoria-y-layout-servicios/home-public-services-layout/spec.md`
- `openspec/changes/layout-cards-servicios/specs/mis-servicios-cliente/customer-services-dashboard/spec.md`
- `openspec/changes/layout-cards-servicios/design.md`
- `openspec/changes/layout-cards-servicios/tasks.md`
- `openspec/changes/layout-cards-servicios/apply-progress.md`
- `openspec/changes/layout-cards-servicios/verify-report.md`

## Sincronización de specs (source of truth)

### `categoria-y-layout-servicios/home-public-services-layout/spec.md` — compose nativo (OK)

```bash
gentle-ai sdd-archive-compose \
  --canonical "openspec/specs/categoria-y-layout-servicios/home-public-services-layout/spec.md" \
  --delta "openspec/changes/layout-cards-servicios/specs/categoria-y-layout-servicios/home-public-services-layout/spec.md" \
  --output "openspec/specs/categoria-y-layout-servicios/home-public-services-layout/spec.md.compose-tmp" \
  && mv "openspec/specs/categoria-y-layout-servicios/home-public-services-layout/spec.md.compose-tmp" "openspec/specs/categoria-y-layout-servicios/home-public-services-layout/spec.md"
```

Exit 0. MODIFIED aplicado sobre `### Requirement: Commercial services public card is state-neutral`: metadata en 3 líneas `mb-2` independientes (Categoría `ti-cloud`/`ti-plant` me-1, Período `ti-calendar-event`, Precio `display-6 fw-bold text-primary` + `<small class="text-secondary">CUP/<período></small>`), 9 escenarios y sección `## Tests a actualizar` preservados. Requisitos no mencionados en el delta ("Two-column image and PDF layout", "PDF trigger keeps modal data attributes") preservados byte-a-byte. Verificación post-compose: 3 líneas `mb-2` + precio `display-6` presentes. NO se editó manualmente (instrucción del orquestador).

### `mis-servicios-cliente/customer-services-dashboard/spec.md` — compose bloqueado + fusión manual aprobada

`gentle-ai sdd-archive-compose` falló (exit 1, sin escritura, atómico — sin `.compose-tmp` residual):

```
Error: sdd-archive-compose: CANONICAL: canonical spec has no "### Requirement:" headings to compose against
```

El repo usa formato canónico `### REQ-XX:`; el tool solo compone contra `### Requirement:`. La fusión MANUAL es el procedimiento establecido del proyecto (esta misma spec se fusionó manualmente en el archive previo de `pulido-ui-servicios`), aprobada explícitamente por el orquestador en el launch.

El delta de este cambio solo MODIFICA `REQ-05: Metadatos normalizados`. Fusión manual: se reemplazó el bloque completo de REQ-05 en la canónica (prosa + tabla + 7 escenarios + nota `(Previously:)`) con el contenido del delta, con UNA desviación intencional: la prosa del delta dice que el último bloque de metadata conserva `mt-auto mb-3`; la canónica refleja LO IMPLEMENTADO (decisión D1 del design): wrapper `d-flex flex-column flex-grow-1 text-secondary mb-3` (pin vía `flex-grow-1`, sin `mt-auto` en la metadata). Esto alinea la prosa con el diseño al promover, tal como recomendaba verify-report (WARNING #2). Verificación por diff programático: el bloque REQ-05 canónico es byte-idéntico al del delta excepto la cláusula del wrapper.

REQ-01 (format_cup), REQ-02, REQ-03, REQ-04 y Coverage Notes: NO modificados; ningún requisito preexistente borrado (5/5 REQ presentes).

## Move a archive

`openspec/changes/layout-cards-servicios/` → `openspec/changes/archive/2026-09-10-layout-cards-servicios/` (ISO 2026-09-10).

- `git mv` falló (directorio sin trackear — `fatal: directorio de fuente está vacío`); fallback `mv` tras verificar snapshot recursivo idéntico al source (diff vacío).
- Readback MANDATORIO: `diff -r <snapshot>/source <destination>` → **vacío (sin diferencias)**, única evidencia de paso. Este `archive-report.md` es aditivo y queda excluido de la comparación (no existía en el snapshot).
- Contenido del archive (7 archivos): `proposal.md`, `design.md`, `tasks.md`, `apply-progress.md`, `verify-report.md`, `specs/categoria-y-layout-servicios/home-public-services-layout/spec.md`, `specs/mis-servicios-cliente/customer-services-dashboard/spec.md`.

## Verificación del archive

- [x] Main specs actualizados (compose nativo + fusión manual)
- [x] Carpeta movida a `openspec/changes/archive/2026-09-10-layout-cards-servicios/`
- [x] Todos los artifacts presentes en el archive
- [x] `tasks.md` archivado: 14/14 `[x]`, sin checkboxes pendientes
- [x] Directorio activo `openspec/changes/` sin `layout-cards-servicios`
- [x] Readback `diff -r` vacío (evidencia en el resultado de fase)

## Claims reconciliados (Final-State Authority)

- **verify-report WARNING #1 (E501 en `test_services_ui.py:737`)**: válido al momento de escribir el reporte; al cierre del ciclo el árbol de trabajo muestra la línea reformateada y `ruff check apps/home/tests/test_services_ui.py` → "All checks passed!". Estado final reportado: limpio (sin commit; restricción del ciclo).
- **verify-report WARNING #2 (prosa `mt-auto mb-3` vs D1)**: resuelto al promover — la canónica `customer-services-dashboard` usa el wrapper `flex-grow-1 mb-3` implementado (fusión manual). La canónica `home-public-services-layout` conserva la prosa del delta (compose nativo; no tocada por instrucción del orquestador); la divergencia permanece documentada en `design.md:21` y ningún escenario aserta `mt-auto`.
- **Sin CRITICALs.** Sin contradicciones entre fuentes sin resolver.

## Estado del ciclo

SDD cycle completo: proposal → spec → design → tasks → apply → verify → archive. `gentle-ai sdd-status layout-cards-servicios --cwd . --json` post-archive: `nextRecommended: archived`, `blockedReasons: []`, `dependencies.archive: all_done`.

## Aditividad

Este `archive-report.md` es el único archivo añadido al archive; no modifica ni elimina ningún artifact del cambio.