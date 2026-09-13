# Archive Report: pulido-ui-servicios

**Date**: 2026-09-10
**Store**: openspec
**Mode**: openspec (filesystem merge + archive folder move)
**Verdict at close**: PASS (21/21 escenarios COMPLIANT, 0 CRITICAL, 548/548 tests)

## Task Completion Gate

- Tasks checked in `tasks.md`: 23/23 `[x]`
- Unchecked implementation tasks: 0
- Gate: PASS

## Verify Report

- Source: `openspec/changes/pulido-ui-servicios/verify-report.md`
- Verdict: PASS
- Critical findings: 0
- Scenarios: 21/21 COMPLIANT
- Tests: 548/548 (exit 0)
- Build: `manage.py check` — 0 issues
- djlint: 0 errors, 0 files to update
- ruff: All checks passed (on changed file)

## Specs Synced

### home-public-services-layout (COMPOSE SUCCESS)

**Canonical**: `openspec/specs/categoria-y-layout-servicios/home-public-services-layout/spec.md`
**Delta**: `openspec/changes/pulido-ui-servicios/specs/home-public-services-layout/spec.md`
**Compose command**: `gentle-ai sdd-archive-compose --canonical ... --delta ... --output ...`
**Result**: Zero exit — composition applied successfully

| Action | Requirement | Details |
|--------|-------------|---------|
| MODIFIED | Commercial services public card is state-neutral | Added: icono diferenciado badge categoría (`ti-cloud`/`ti-plant`), sin `ti-currency-dollar`, sin bloque "Código:"; 4 new scenarios added (Precio sin icono dollar, Sin bloque código, Badge categoría pronóstico, Badge categoría agrometeo) |
| PRESERVED | Two-column image and PDF layout | Unchanged — 2 scenarios |
| PRESERVED | PDF trigger keeps modal data attributes | Unchanged — 1 scenario |

### customer-menu-notifications (COMPOSE BLOCKED)

**Canonical**: `openspec/specs/mis-servicios-cliente/customer-menu-notifications/spec.md`
**Delta**: `openspec/changes/pulido-ui-servicios/specs/customer-menu-notifications/spec.md`
**Compose result**: BLOCKED — `sdd-archive-compose` requires `### Requirement:` headings in canonical spec; canonical uses `### REQ-09:` / `### REQ-10:` format
**Delta preserved in archive**: `openspec/changes/archive/2026-09-10-pulido-ui-servicios/specs/customer-menu-notifications/spec.md`

Pending delta content (not yet applied to canonical):
- MODIFIED REQ-09: badge father replaces dot; badges migrate to "Mis Servicios"; "Servicios Comerciales" sin badges
- MODIFIED REQ-10: badge `bg-red-lt` replaces dot animado
- REMOVED REQ-10 (anterior): dot animado funcional

### customer-services-dashboard (COMPOSE BLOCKED)

**Canonical**: `openspec/specs/mis-servicios-cliente/customer-services-dashboard/spec.md`
**Delta**: `openspec/changes/pulido-ui-servicios/specs/customer-services-dashboard/spec.md`
**Compose result**: BLOCKED — `sdd-archive-compose` requires `### Requirement:` headings in canonical spec; canonical uses `### REQ-01:` through `### REQ-05:` format
**Delta preserved in archive**: `openspec/changes/archive/2026-09-10-pulido-ui-servicios/specs/customer-services-dashboard/spec.md`

Pending delta content (not yet applied to canonical):
- MODIFIED REQ-04: fix factura owner access (`commercial:factura_download/<uuid>?inline=1`); iconos diferenciados; sin `ti-currency-dollar`; 5 scenarios
- MODIFIED REQ-05: layout uniforme fechas→pago→precio; sin `ti-currency-dollar`; 3 scenarios

## Archive Move

- **Source**: `openspec/changes/pulido-ui-servicios/`
- **Destination**: `openspec/changes/archive/2026-09-10-pulido-ui-servicios/`
- **Method**: `git mv` failed (directory not tracked), fell back to `mv`
- **Readback**: `diff -r` — empty (no differences) ✅

### diff -r readback (archive move)

```
(no output — empty diff confirms byte-identity)
```

## Archive Contents

| Artifact | Status | Size |
|----------|--------|------|
| proposal.md | ✅ Present | 6,527 bytes |
| design.md | ✅ Present | 7,175 bytes |
| tasks.md | ✅ Present (23/23 [x]) | 4,744 bytes |
| apply-progress.md | ✅ Present | 7,997 bytes |
| verify-report.md | ✅ Present | 14,607 bytes |
| specs/customer-menu-notifications/spec.md | ✅ Present (delta) | — |
| specs/customer-services-dashboard/spec.md | ✅ Present (delta) | — |
| specs/home-public-services-layout/spec.md | ✅ Present (delta) | — |

## Final State

### What shipped

The `pulido-ui-servicios` change polished the UI for the commercial services section:
1. **Menu badges**: Parent "Servicios" toggle shows `bg-red-lt` badge (replaces animated dot); child "Mis Servicios" shows `bg-blue-lt` (requested) and `bg-orange-lt` (pending) badges; "Servicios Comerciales" no longer shows state badges
2. **Card actions**: "Ver factura" button points to `commercial:factura_download/<uuid>?inline=1` (fixes 403); payment icons differentiated (QR/bank/store)
3. **Price display**: Removed redundant `ti-currency-dollar` from both Mis Servicios and public catalog cards
4. **Public catalog**: Category badges with differentiated icons (`ti-cloud`/`ti-plant`); removed "Código:" block
5. **Error pages**: 400/403/404/500 pages now have `history.back()` with `home:index` fallback
6. **Tests**: 54 tests in `test_services_ui.py` (5 unit + 49 integration), all passing

### Outstanding: compose blocking

2 of 3 delta specs could not be composed into canonical specs due to heading format mismatch (`### REQ-XX:` vs `### Requirement:`). The deltas are preserved in the archive and can be applied when the compose tool is updated to support `### REQ-XX:` headings, or when the canonical specs are normalized to use `### Requirement:` headings.

## Skills Referenced

- `sdd-archive` (v2.0) — loaded, followed
- `sdd-phase-common` — Section A (load), Section C (persistence)
