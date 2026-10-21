# Archive Report — 024-deploy-check-fail-closed

**Change**: 024-deploy-check-fail-closed
**Archived**: 2026-10-11
**Archive location**: `openspec/changes/archive/2026-10-11-024-deploy-check-fail-closed/`
**Artifact store**: openspec (filesystem)
**Archived by**: `sdd-archive` phase

## Final State

Reported at close, per the Final-State Authority hierarchy (persisted tasks artifact >
launch-prompt facts > intermediate snapshots).

| Item | Final value | Source |
|------|-------------|--------|
| Tasks complete | **12/14** (unchecked: `3.3 Commit`, `3.4 Archivar`) | persisted `tasks.md` |
| Verify verdict | **not run** — no `verify-report.md` artifact exists | artifact absent |
| Code changes | **none** — the change only synchronises the spec | `proposal.md` |
| Artifact commit | `c7d5c32 docs(openspec): sincronizar 013-check-deploy-ci con el codigo actual` (3 files, +287) | `git show --stat c7d5c32` |
| Main spec after promotion | `openspec/specs/013-check-deploy-ci/spec.md`, 286 lines, sha256 `b1c1f4fd811e4469…` | `sha256sum` |

### Unfinished tasks, recorded without repair

The archived `tasks.md` retains its original bytes: `3.3` and `3.4` remain unchecked and were
**not** retroactively ticked, per the Honest Partial Archive rule.

- **`3.3 Commit`** — materially satisfied before this archive: all three change artifacts were
  committed in `c7d5c32`. The checkbox was left as the prior phase persisted it.
- **`3.4 Archivar con \`gentle-ai sdd-archive\` para promover el delta sobre
  \`openspec/specs/013-check-deploy-ci/\`** — satisfied by this archive, but **not** through the
  command the task names; see Composition Method.

## Acceptance Criteria (from `proposal.md`), verified against the promoted spec

| Criterion | Observed | Evidence |
|-----------|----------|----------|
| `013-check-deploy-ci` no longer names `manage.py generate_env` in any requirement | **0 occurrences** | `grep -c 'manage.py generate_env'` |
| `013-check-deploy-ci` no longer names `EphemeralSecretKeyWarning` | **0 occurrences** | `grep -c 'EphemeralSecretKeyWarning'` |
| The fail-closed requirement covers dev, production and the `testing` exception | **present** | `### Requirement: Settings Fail Closed Without Decryptable Key Material` (4 scenarios) |
| The external-generator requirement explains why a management command would not work | **present** | `### Requirement: Key Material Generation Lives Outside Django` (2 scenarios) |

Result: 9 requirements, 28 scenarios, 286 lines.

## Specs Synced

| Canonical | Action | Details |
|-----------|--------|---------|
| `openspec/specs/013-check-deploy-ci/spec.md` | Updated (composed) | 2 requirements MODIFIED in place, 1 REMOVED, 3 ADDED at the end; 4 unrelated requirements preserved byte-for-byte |

### Composition Method

The native composition command mandated by the `sdd-archive` skill was **invoked first and is
unavailable in the installed toolchain**:

```
$ gentle-ai sdd-archive-compose --help
Error: unknown command "sdd-archive-compose" — run 'gentle-ai help' for available commands
```

`gentle-ai 4.0.0` (binary dated 2026-10-04) exposes only `review *`, `sync`, `install` and
`skill-registry`; the skill that requires the verb is dated 2026-09-27. `gentle-ai sync` was run
and reported `Sync actions executed: 1 files changed` (`opencode.jsonc`) — it did **not** refresh
the skills, so the skew persisted. There is no `openspec` binary on this machine either. That the
verb once existed here is evidenced by
`archive/2026-09-10-pulido-ui-servicios/archive-report.md` (a real invocation) and
`archive/2026-09-10-layout-cards-servicios/archive-report.md` (recorded `exit 1`).

Because the canonical already existed and carried unrelated requirements that had to survive,
composition followed the project's own documented precedent
(`archive/2026-09-16-categoria-y-layout-servicios/archive-report.md`): a **deterministic `sed`
range composition**. No artifact byte ever passed through a model Read/Write path. The output file
was built in a single pass to `spec.md.compose-tmp` and was only promoted with `mv` after every
one of the six verification diffs came back **EMPTY**:

| Check | Result |
|-------|--------|
| head, out `1–65` vs canonical `1–65` | EMPTY |
| MODIFIED `CI Generates Its Own Secret Key Material`, out `66–115` vs delta `5–54` | EMPTY |
| preserved `Production Security Posture Hardened`, out `116–146` vs canonical `131–161` | EMPTY |
| MODIFIED `Production Rejects The Console Email Backend`, out `147–180` vs delta `55–88` | EMPTY |
| preserved `Existing CI Jobs Are Not Broken`, out `181–198` vs canonical `196–213` | EMPTY |
| ADDED block, out `200–286` vs delta `109–195` | EMPTY |

The REMOVED requirement `Ephemeral SECRET_KEY Fallback Warns` (canonical `94–130`) was dropped
whole; its absence is confirmed by `grep -c 'Ephemeral SECRET_KEY Fallback Warns'` → **0**, and
the delta's `(Reason: …)` / `(Migration: …)` notes are preserved inside the archived delta spec.

`rules.archive` from `openspec/config.yaml` ("Warn before merging destructive deltas") was
honoured: the destructive removal was surfaced to the maintainer, who authorised the archive
explicitly before any spec byte was written.

### Requirement order in the promoted canonical

Preserved originals in place, MODIFIED replaced in place, ADDED appended at the end:

1. `CI Runs Deployment System Checks`
2. `Job Fails On Any Warning Or Error`
3. `CI Generates Its Own Secret Key Material` *(MODIFIED)*
4. `Production Security Posture Hardened`
5. `Production Rejects The Console Email Backend` *(MODIFIED)*
6. `Existing CI Jobs Are Not Broken`
7. `Key Material Generation Lives Outside Django` *(ADDED)*
8. `Settings Fail Closed Without Decryptable Key Material` *(ADDED)*
9. `The Decryption Key Is Not Stored Beside The Ciphertext` *(ADDED)*

## Archive Contents

- `proposal.md` ✅ present
- `specs/013-check-deploy-ci/spec.md` ✅ present
- `design.md` — absent (the change carried no technical design)
- `tasks.md` ✅ present, 12/14 complete; 2 unfinished (`3.3`, `3.4`)
- `verify-report.md` — absent (verification not run for this change)

Folder move readback: pre-move recursive snapshot vs archived tree → `diff -r` **EMPTY**.

## Source of Truth Updated

- `openspec/specs/013-check-deploy-ci/spec.md`

## Persistence

Filesystem write succeeded (see readbacks above). The Engram mirror
(`sdd/024-deploy-check-fail-closed/archive-report`) was **not** persisted: the Engram server could
not confirm session registration during this session. Recorded as an outstanding mirror, not as a
success.

## SDD Cycle Complete

The change is archived and `013-check-deploy-ci` now describes what the code actually does.
Implementation: no code was touched by this change — it is a contract synchronisation.
Verification: **not run** (no `verify-report.md`); substantiated instead by direct inspection of the
four requirements against the code at promotion time, as recorded in `proposal.md` and `tasks.md`
`2.1`–`2.6`.
Unfinished tasks: `3.3 Commit` (materially satisfied by `c7d5c32`) and `3.4 Archivar` (satisfied by
this archive, via the documented fallback rather than the named command). No unresolved findings.
