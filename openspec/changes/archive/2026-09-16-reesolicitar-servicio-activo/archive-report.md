# Archive Report — reesolicitar-servicio-activo

**Change**: reesolicitar-servicio-activo
**Capability**: `service-re-request` — a client can re-request a commercial service while an active (paid) subscription exists; a new `requested` row is created and only in-flight (`requested`/`pending`) subscriptions block submission
**Archive date**: 2026-09-16
**Mode**: openspec filesystem (native dispatcher reported `artifactStore: openspec`) + Engram archive-report (hybrid, per session preflight and this cycle's persistence pattern)

## Final-state facts

| Fact | Value | Source |
|------|-------|--------|
| Verify verdict | PASS — `gentle-ai.verify-result/v1` `verdict: pass`, `critical_findings: 0`, `blockers: 0` | persisted `verify-report.md` (read pre-move from `openspec/changes/reesolicitar-servicio-activo/verify-report.md`); ledger attempt ordinal 4 `outcome: passed` |
| Requirements | 4/4 (REQ-01, REQ-02, REQ-04, REQ-06) | `verify-report.md` (`requirements: 4/4`) + amended delta spec (4 `### Requirement:` headings) |
| Scenarios | 7/7 | `verify-report.md` (`scenarios: 7/7`) + amended delta spec (7 `#### Scenario:` headings) |
| Tests — change classes | 17/17 (exit 0) | `verify-report.md` (at verification time) |
| Tests — affected apps | 392/392 (exit 0) | `verify-report.md` (at verification time) |
| Tests — full suite | 743/743 (exit 0) | `verify-report.md` + orchestrator launch prompt (final state) |
| Build | `python manage.py check` exit 0 | `verify-report.md` |
| Lint | ruff clean (exit 0), djlint 0 errors | `verify-report.md` |
| Migrations | None (REQ-06: no schema change) | `verify-report.md` compliance matrix |
| Tasks | 20/20 `[x]`, 0 unchecked | persisted `tasks.md` (Task Completion Gate, read pre-move; archived copy byte-identical per `diff -r` readback; `grep -cE '^\s*- \[ \]'` = 0) |
| Runtime ledger | `complete: true`, `decision_required: false`, `next_action: complete` | `gentle-ai sdd-attempt status` at archive time — no attempt operation needed for archive |
| Native status | `dependencies.archive: ready`, `nextRecommended: archive`, `blockedReasons: []`, `notes: []`, `applyState: all_done` | `gentle-ai sdd-status --json --instructions` at archive time |
| Review transition | `unrelated` / `next_transition: stop (rdd_disabled)` — no action | `gentle-ai review status --next-transition --contract gentle-ai.review-integration/v2` |

## Evidence revision resolution (consistent — no contradiction)

- Orchestrator launch prompt cites evidence revision `sha256:e28c018e…`. **Independently verified**: `sha256sum` of the persisted `verify-report.md` = `e28c018ee19378fd0695d160010e4842bcb92fbd06e13c56f9de79f584742535`, matching both the launch prompt and the ledger's ordinal-4 `evidence_revision`. The file on disk IS the passing report (not a stale draft).
- The YAML header inside `verify-report.md` declares `evidence_revision: sha256:055a0cc0e4497f908401aeabb64b3c8f9219d69aaac279b1064c6ba96591c440` — the report's internal attestation field. The bytes were admitted by `gentle-ai sdd-verify-validate` (`valid: true, verdict: pass`, per ledger ordinal-4 process evidence). I attempted to reproduce `055a0cc0…` as a digest over proposal/spec/design/tasks in 8 orderings (with/without trailing newlines, with/without `exploration.md`) — none matched. Recorded transparently; non-blocking, because no authoritative source (launch prompt, ledger, file hash) contradicts `e28c018e…` as the evidence revision, and the validator admitted the header bytes.
- Cross-check: `sha256` of the amended delta spec (and of the promoted canonical) = `c32f22ff3b79a7446b3700daf85b8ef3fa8ecc1544a64a2bf0331bd16a4f692a`, which equals the ledger's ordinal-3 `evidence_revision` (spec-amendment attempt). Consistent.

## Verification snapshot (per `verify-report.md`, persisted at verification time)

- Compliance: REQ-01 (re-request creates `requested` row, existing `paid` row untouched, redirect to `commercial:suscripcion_list`; form with "Solicitar" label + active-until alert), REQ-02 (blocked on `requested`/`pending`: no new row, warning, redirect; form and submit button hidden), REQ-04 (context splits into `in_flight_subscription`/`active_subscription`, `existing_subscription` removed), REQ-06 (no schema change, `(customer, service)` pairing remains non-unique) — all ✅ COMPLIANT, 7/7 scenarios.
- **0 CRITICAL, 0 blockers.**

### Non-blocking warnings (from `verify-report.md`; recorded for audit — the report itself marks them non-blocking and the ledger's remediation accepted them)

1. Design deviation D3 — deterministic per-service `user_subscriptions` resolver absent at HEAD; the public catalog is state-neutral. Zero spec impact after the 2026-09-16 amendment (REQ-05 removed; catalog neutrality owned by the promoted spec `home-public-services-layout`).
2. TDD Cycle Evidence table absent from apply evidence (`applyProgress` locator unresolved) — historical process-evidence gap from the apply phase, downgraded from CRITICAL to WARNING by the maintainer's remediation; RED/GREEN re-verified live in the final run.

### Suggestions (from `verify-report.md`, not addressed in this archive)

1. Strengthen the submit-button label assertion in `test_active_paid_renders_form_and_cta` (weak `assertIn('Solicitar', html)`).
2. Add direct context-level assertions for REQ-04 S1.
3. Assert the success-path redirect explicitly (`assertRedirects`).
4. Clean stale test comments referencing REQ-06/REQ-07 numbering that match no open spec.

## Specs synced

| Domain | Action | Details |
|--------|--------|---------|
| `reesolicitar-servicio-activo` | Created (main spec did not exist — delta IS the full spec) | `openspec/specs/reesolicitar-servicio-activo/spec.md` — 4 requirements / 7 scenarios, `### Requirement:` / `#### Scenario:` standard |

Mechanical copy via shell (`cp` to temp → `diff -r` readback → `mv`); verbatim readback empty (byte-identical promotion, sha `c32f22ff…` both sides). No merge against a pre-existing main spec; no unrelated requirements at risk; native composition (`sdd-archive-compose`) was not applicable because the canonical did not exist. `rules.archive` from `openspec/config.yaml` ("Warn before merging destructive deltas") — N/A: additive promotion, nothing destructive.

## Archive contents

- `proposal.md` ✅
- `specs/reesolicitar-servicio-activo/spec.md` ✅
- `design.md` ✅
- `tasks.md` ✅ (20/20 tasks complete, 0 unchecked)
- `verify-report.md` ✅
- `exploration.md` ✅ (optional artifact, moved with folder)
- `archive-report.md` ✅ (this file, additive — excluded from the readback by contract)

Archive move performed as one shell transaction: pre-move recursive snapshot → `git mv` (tracked files staged as renames; `verify-report.md` untracked by design, moves as plain file) → mandatory `diff -r snapshot-vs-destination` readback (**EMPTY, exit 0**). Source directory confirmed absent from `openspec/changes/`. No temp/compose leftovers in either destination.

## Source of truth updated

- `openspec/specs/reesolicitar-servicio-activo/spec.md`

## Traceability (hybrid store)

Artifacts were read from filesystem paths per the native dispatcher's openspec locators (`proposal.md`, `specs/reesolicitar-servicio-activo/spec.md`, `design.md`, `tasks.md`, `verify-report.md` — all read pre-move). No Engram observations were read as source material for this archive. Engram observations referenced by this cycle's ledger, listed for cross-reference: #243 (spec topic — persisted 2026-09-07, predates the 2026-09-16 amendment; the amended bytes are the filesystem file, sha `c32f22ff…`), #312 (verify PASS + settle mirror), plus #240/#241/#242/#244/#245/#246/#248 (exploration/proposal/design/tasks/apply history). Archive report persisted as Engram topic `sdd/reesolicitar-servicio-activo/archive-report` (type `architecture`, `capture_prompt: false`).

## Notes / risks observed at archive time

- Concurrent archive activity in the same repository during this run: `servicios-activacion-filtro-home` was moved to `openspec/changes/archive/2026-09-16-servicios-activacion-filtro-home/` by another actor (staged renames observed mid-run). It is a different change; no destination collision or interference with this archive's paths was detected.

## SDD Cycle Complete

The change has been fully planned, implemented, verified, and archived.
