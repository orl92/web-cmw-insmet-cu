# Archive Report — categoria-y-layout-servicios

**Change**: categoria-y-layout-servicios
**Archived**: 2026-09-16
**Archive location**: `openspec/changes/archive/2026-09-16-categoria-y-layout-servicios/`
**Artifact store**: hybrid (OpenSpec filesystem + Engram observation)
**Archived by**: `sdd-archive` phase

## Final State

Reported at close, per the Final-State Authority hierarchy (persisted tasks artifact > explicit launch-prompt facts > intermediate `verify-report`/`apply-progress` snapshots).

| Item | Final value | Source |
|------|-------------|--------|
| Tasks complete | 22/22 (0 unchecked) | persisted `tasks.md` (grep: 22 `[x]`, 0 `[ ]`) |
| Verify verdict | **PASS** | `verify-report.md` (`gentle-ai.verify-result/v1`, `verdict: pass`) |
| Requirements | 6/6 | `verify-report.md` (snapshot at verify time) |
| Scenarios | 13/13 | `verify-report.md` (snapshot at verify time) |
| CRITICAL issues | 0 | `verify-report.md` |
| Full test suite | 743 passed, 0 failed (`python manage.py test`, exit 0) | `verify-report.md` (`test_output_hash: sha256:8618feb1…`) |
| Build check | `python manage.py check` exit 0 | `verify-report.md` (`build_output_hash: sha256:1e3e63f2…`) |
| Lint/templates | ruff 0, djlint 0 | `verify-report.md` |
| Evidence revision | `sha256:52d29382145953995f37f9cd53a4756ea2a6d9cca1fcd2c5aec4dba4109d2114` | `verify-report.md` |

No CRITICAL issues were present at verification time; no override or reconciliation was required. The Task Completion Gate passed on the persisted artifact (22/22 checked, verified by `grep`, matching native status `taskProgress.total: 22, completed: 22, allComplete: true`).

## Specs Synced

| Canonical | Action | Details |
|-----------|--------|---------|
| `openspec/specs/categoria-y-layout-servicios/commercial-service-categories/spec.md` | Rewritten (composed) | 153 lines; 7 requirements, 1 Coverage Notes section |

The change carried exactly **one** delta spec: `specs/commercial-service-categories/spec.md` (136 lines, 6 requirements, 13 scenarios). No `specs/home-public-services-layout/` directory exists in the change (see Contradiction Record below).

### Composition Method

The native composition command was invoked first and **refused by design**:

```
gentle-ai sdd-archive-compose \
  --canonical "openspec/specs/categoria-y-layout-servicios/commercial-service-categories/spec.md" \
  --delta     "openspec/changes/categoria-y-layout-servicios/specs/commercial-service-categories/spec.md"
→ exit 1: "DELTA: delta spec declares no ADDED, MODIFIED, REMOVED, or RENAMED requirements"
```

This refusal is a **tool-domain mismatch, not a spec defect**: `sdd-archive-compose` operates on OpenSpec marker-style deltas (ADDED/MODIFIED/REMOVED/RENAMED). This delta is a **full spec** (no markers), which the skill's contract routes to the full-spec branch. Because a canonical already existed at the repo-convention path with one foreign requirement that must survive, the archive used a **mechanical shell composition** (no model Read/Write ever touched artifact bytes):

1. `sed -n '1,130p'` of the delta → header + Purpose + 6 corrected requirements (ends with blank line).
2. `sed -n '55,70p'` of the pre-existing canonical → the preserved foreign requirement block.
3. One blank separator line.
4. `sed -n '131,136p'` of the delta → the corrected Coverage Notes.

Verification (all diffs **EMPTY**):

| Check | Result |
|-------|--------|
| out lines 1–130 vs delta lines 1–130 | EMPTY |
| out lines 131–146 vs canonical lines 55–70 (preserved block) | EMPTY |
| out lines 148–153 vs delta lines 131–136 (Coverage Notes) | EMPTY |
| whole file vs composition built from the same sources | EMPTY |

Resulting canonical: 153 lines = 130 (delta requirements) + 16 (preserved requirement block) + 1 (blank) + 6 (Coverage Notes).

### Requirements: Added / Removed / Preserved

**Added (6 corrected requirements, from the delta):**
- Category select visible only for commercial type in create form
- Category select visible only for commercial type in update form
- Public services render PDF and image side by side in the form
- Image required for public services
- Balanced first row (title + type)
- Commercial fields in one balanced row (category, code, price)

**Removed (3 stale pre-correction requirements with reverted scope):**
- Service category select in create form — *removed: "always visible" scope was reverted*
- Service category select in update form — *removed: "always visible" scope was reverted*
- Category select applies to public and commercial services — *removed: the change reverted to commercial-only*

These three existed only because the canonical was created at planning time (`bea19e4`, 2026-09-09) carrying the pre-correction scope. This archive corrects them. The stale Coverage Note "Commercial services billing layout is out of scope; only the service form exposes the category" was likewise replaced by the delta's corrected notes.

**Preserved (byte-for-byte, not this change's property):**
- `### Requirement: Public card exposes category badge and discrete code` + its 2 scenarios — owned by the archived change **mis-servicios-cliente** (commit `8bbe111`), which promoted it into this canonical. The delta does not mention or remove it, so it was preserved verbatim (canonical lines 55–70). The `mis-servicios-cliente` archive references this canonical as the governing spec, so dropping it would have corrupted that audit trail.

## Archive Contents

- `proposal.md` ✅
- `specs/commercial-service-categories/spec.md` ✅
- `design.md` ✅
- `tasks.md` ✅ (22/22 complete, 0 unchecked)
- `verify-report.md` ✅ (PASS)
- `archive-report.md` ✅ (this file, additive)

### What Was Not Moved

`openspec/specs/categoria-y-layout-servicios/home-public-services-layout/spec.md` was **not touched**. This change produced no delta for that domain; the canonical retains the requirements promoted by previous archives (e.g. `mis-servicios-cliente`).

## Mechanical Verification Evidence

**Canonical composition** — segment diffs listed above: all EMPTY.

**Archive move** — `git mv` succeeded for all tracked artifacts; the mandatory `diff -r` readback of the pre-move recursive snapshot against the archived destination returned:

```
=== MANDATORY readback: diff -r snapshot vs destination (only EMPTY passes) ===
READBACK EMPTY (pass)
```

No differences, no truncation, no alteration. The source directory no longer exists after the move; the active `openspec/changes/` directory contains only `archive/`. `archive-report.md` is additive and therefore excluded from the snapshot comparison.

## Contradiction Record

- **Launch context vs. repository evidence**: the archive launch context mentioned a second spec, `specs/home-public-services-layout/spec.md`, as if it existed in the change. It does not — the directory is absent from the change root and from native `artifactPaths.specs`, which lists only `commercial-service-categories`. `verify-report.md` records the same finding independently. Resolution: nothing to promote for that domain; the mention is recorded here rather than silently acted upon. No repository action was taken for a non-existent artifact.
- **Artifact store**: the launch context declared `hybrid`; native `gentle-ai sdd-status` reported `artifactStore: openspec`. Both conventions were satisfied — OpenSpec filesystem sync/move plus an Engram observation for this report. No conflict in outcome.

## Notes Carried Forward (non-blocking)

From `verify-report.md`, attributed to that snapshot at verification time:

- **WARNING** — `apply-progress` artifact missing, so the strict-TDD Cycle Evidence table could not be cross-verified from an apply-phase artifact; TDD substance was independently confirmed (tasks test markers, test files present, green execution). Classified as a process/artifact gap, not an implementation failure. This is a workspace-wide gap (only a minority of changes produce `apply-progress.md`).
- **SUGGESTION** — `toggleFields()` client-side show/hide behavior has static (template) coverage only; no browser-level JS test exists (Django TestCase cannot execute JS).
- **SUGGESTION** — commit `1053af5` containing this change's implementation is a large mixed commit (31 files) spanning unrelated features; the change's own 5-file set is within the 400-line review budget.

## SDD Cycle Complete

The change was planned, implemented, verified (PASS), and archived. Delta specs were synced to the canonical before the move, preserving unrelated requirements. No CRITICAL verification issues and no stale unchecked tasks were present, so no override or reconciliation was applied.
