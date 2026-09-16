# Archive Report — servicios-activacion-filtro-home

**Change**: servicios-activacion-filtro-home
**Capability**: Filtro por estado en home + reactivación desde listado + bloqueo de tipo en edición + layout de cards y listado
**Archive date**: 2026-09-16
**Mode**: hybrid (openspec filesystem + Engram archive-report)

## Final-state facts

| Fact | Value | Source |
|------|-------|--------|
| Verify verdict | PASS WITH WARNINGS (0 CRITICAL, 0 blockers, verdict `pass`) | persisted `verify-report.md` — the final re-verify run, evidence `sha256:fb7d745ab665838a66cafafe8773bb1d8feab362f8514274d2a3c59e4d4a3ef5`; confirmed by orchestrator launch prompt ("re-verify PASÓ … evidencia `fb7d745a…`, suite completa 743 OK") |
| Requirements | 6/6 | `verify-report.md` + repository evidence (grep-verified 6 `### Requirement:` in promoted canonical spec) |
| Scenarios | 10/10 (8 fully asserted at runtime, 2 with static-negative clauses flagged WARNING) | `verify-report.md` + repository evidence (grep-verified 10 `#### Scenario:` in promoted canonical spec) |
| Tests | 743/743 (exit 0, full suite `python manage.py test`); scoped `apps.commercial apps.home` 392 OK | `verify-report.md` |
| Build | `manage.py check` clean (exit 0) | `verify-report.md` |
| Lint | ruff + djlint clean (exit 0) | `verify-report.md` |
| Tasks | 16/16 `[x]`, 0 unchecked | persisted `tasks.md` (Task Completion Gate) |
| Spec amendment | Delta spec amended to real HEAD state by maintainer decision: REQ-6 equal-height cards (`h-100`) withdrawn; commercial price cell specified as `format_cup` | `verify-report.md` Scope Note + spec Coverage Notes |
| Native status | `dependencies.archive: ready`, `nextRecommended: archive`, `taskProgress: 16/16 allComplete: true`, `blockedReasons: []`, `actionContext.mode: repo-local` | `gentle-ai sdd-status servicios-activacion-filtro-home` at archive time |

## Attempt ledger state (no new intent opened)

- `gentle-ai sdd-attempt status` at archive time: `complete: true`, `next_action: complete`, `decision_required: false`, `cumulative_attempts: 2` — the change's attempt ledger is closed; the preflight instruction "NO abras un intent nuevo si no es necesario" was followed, no `begin`/`finish`/`reset`/`settle` run.
- Attempt 1 (work_unit `verify-servicios-activacion-filtro-home`, gen 1): outcome `failed`, evidence `sha256:51145924…` — REQ-6 h-100 unimplemented and untested; superseded by the amended-spec objective.
- Attempt 2 (work_unit `spec-enmienda-estado-real`, gen 2): outcome `passed`, evidence `sha256:d447e9415b…` recorded at attempt finish.
- Review lifecycle: `gentle-ai review status --next-transition` returns `kind: stop`, `reason_code: rdd_disabled` (forecast terminal) — no review transition to route; delivery follows ordinary repository policy. Untracked candidates (`verify-report.md`, archive files, promoted spec) are inventory `sha256:4c9dfdd3ec2fb72b95824094e8dc3d535eebf82c371b0746669d5a6601785493`, no lifecycle operation required.

## Evidence revision resolution (traceability note, no contradiction)

- `sha256:fb7d745ab665838a66cafafe8773bb1d8feab362f8514274d2a3c59e4d4a3ef5` is the `evidence_revision` declared in the YAML header of the persisted `verify-report.md` — re-admitted at archive time by `gentle-ai sdd-verify-validate --input verify-report.md --requirements 6 --scenarios 10` → `valid: true, verdict: pass`. It is the verification evidence identity, confirmed by the orchestrator launch prompt as the final re-verify evidence. It is neither the report file's own sha (`26d0f68c…`) nor any simple proposal+spec+design+tasks concatenation (checked at archive time).
- `sha256:d447e9415b35fad849cf021483fad4acd2597337435cfb2876a3c008de74ae0a` recorded by the attempt ledger as attempt-2 (spec-enmienda) `evidence_revision` **equals the sha256 of the amended spec file itself** — verified at archive time: `sha256(openspec/specs/servicios-activacion-filtro-home/spec.md) = d447e9415b…`. The spec-enmienda attempt's evidence was the amended spec bytes; the final re-verify produced the report carrying `fb7d745a`. Both facts are consistent; no conflict recorded.

## Verification snapshot (per `verify-report.md`, final re-verify evidence `fb7d745a`)

- **6/6 requirements** — REQ-1 public list filter, REQ-2 public commercial list filter, REQ-3 detail+related active-only, REQ-4 reactivation, REQ-5 type immutable on edit, REQ-6 public rows em-dash (amended wording).
- **10/10 scenarios** with covering tests executed at runtime (16 change-related tests across `apps/home/tests/test_services_ui.py` + `apps/commercial/tests/test_views.py`).
- **No CRITICAL findings, 0 blockers.**

### Non-blocking warnings (from `verify-report.md`, recorded for audit)

1. REQ-4 "Reactivate button gated by state and permission": covering test asserts the control renders for an inactive row (with `change_service`) but not its absence on active rows nor the permission-negative case; the template condition `{% if not object.record_active and perms.commercial.change_service %}` is statically correct for both negative branches.
2. REQ-4 "Reactivating an already active service is a no-op warning": covering test asserts state unchanged but not the warning message; the view emits `messages.warning(request, 'El servicio ya estaba activo.')` in the executed branch (statically confirmed).
3. `apply-progress` artifact missing (`artifactPaths.applyProgress` empty, native `artifacts.applyProgress: missing`): Strict TDD apply phase did not persist the TDD Cycle Evidence report; RED/GREEN/Triangulation independently confirmed by the verification run (4 test classes exist, 743/743 pass). Process-persistence gap only, does not block archive.

### Task-completion note (from `verify-report.md`, final state)

Task 4.1 (`card h-100` in create/update) is marked `[x]` but describes the withdrawn REQ-6: the class is absent from `create.html`/`update.html` and the maintainer decided not to implement it (spec Coverage Notes) — no spec violation under the amended spec; recorded here for audit completeness of the 16/16 gate.

### Suggestions (from `verify-report.md`)

1. Extend `test_reactivate_button_only_for_inactive_services` with negative assertions (active row omits control; user without `change_service` sees none) and assert the warning message in the no-op test.
2. If the equal-height PDF/image cards layout (`h-100`) is ever wanted, spec and implement it as a separate change: the amended spec deliberately excludes it.

## Specs synced

| Domain | Action | Details |
|--------|--------|---------|
| `servicios-activacion-filtro-home` | Created (main spec did not exist — delta IS the full spec) | `openspec/specs/servicios-activacion-filtro-home/spec.md` — 6 requirements / 10 scenarios, h3 `### Requirement:` / h4 `#### Scenario:` standard |

Mechanical copy via shell (`cp` → `diff -r` readback → `mv`, with `mktemp` intermediate for atomic write); verbatim readback diff was empty (byte-identical promotion). No merge against a pre-existing main spec was required; no unrelated requirements were at risk of alteration. `chmod 664` applied to the promoted file to match repo convention (content untouched; byte identity re-verified after chmod with an empty `diff -r`).

## Archive contents

- `proposal.md` ✅
- `specs/servicios-activacion-filtro-home/spec.md` ✅
- `design.md` ✅
- `tasks.md` ✅ (16/16 tasks complete, 0 unchecked)
- `verify-report.md` ✅
- `archive-report.md` ✅ (this file, additive — excluded from the mechanical readback by design)

Archive move performed as one shell transaction: pre-move recursive snapshot → `git mv` (succeeded on git 2.43.0, carrying the untracked `verify-report.md` along) → mandatory `diff -r` snapshot-vs-destination readback (empty, exit 0). Source directory confirmed absent from `openspec/changes/`.

## Source of truth updated

The following spec now reflects the new behavior (full capability spec promoted):
- `openspec/specs/servicios-activacion-filtro-home/spec.md`

## Traceability (hybrid store)

Artifacts were read from filesystem paths (`openspec/changes/servicios-activacion-filtro-home/…`, per the dispatcher's openspec locators): `proposal.md`, `specs/servicios-activacion-filtro-home/spec.md`, `design.md`, `tasks.md`, `verify-report.md`; no Engram observation IDs were read for this archive. Archive report persisted to Engram `sdd/servicios-activacion-filtro-home/archive-report` (hybrid).

**Concurrent worktree observation (not performed by this archive):** during this archive, `reesolicitar-servicio-activo` was independently moved to `openspec/changes/archive/2026-09-16-reesolicitar-servicio-activo/` (own `archive-report.md`, own promoted canonical `openspec/specs/reesolicitar-servicio-activo/spec.md`). This sub-agent's transactions were scoped strictly to `servicios-activacion-filtro-home`; the concurrent move is reported for delivery awareness, not modified or verified here.

## SDD Cycle Complete

The change has been fully planned (amended spec), implemented, verified (PASS with warnings — re-verify `fb7d745a`, 743 OK), and archived.
