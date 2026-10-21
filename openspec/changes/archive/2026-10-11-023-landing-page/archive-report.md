# Archive Report — 023-landing-page

**Change**: 023-landing-page
**Archived**: 2026-10-11
**Archive location**: `openspec/changes/archive/2026-10-11-023-landing-page/`
**Artifact store**: openspec (filesystem)
**Archived by**: `sdd-archive` phase

## Final State

Reported at close, per the Final-State Authority hierarchy (persisted tasks artifact >
launch-prompt facts > intermediate snapshots).

| Item | Final value | Source |
|------|-------------|--------|
| Tasks complete | **37/37** (0 unchecked) | persisted `tasks.md`, `grep -c '^- \[x\]'` |
| Verify verdict | **not run** — no `verify-report.md` artifact exists | artifact absent |
| Code changes | merged; `860210d Merge pull request #74 from orl92/feat/landing-page` is an ancestor of `main` and `origin/main` | `git merge-base --is-ancestor 860210d main` → true |
| Implementation commits | 8 named by the change (see below) | `git log --grep='023-landing-page'` |

Implementation commits (oldest → newest):

```
cb0a107 feat(home): activa footers sociales social-gray público y dashboard
7462b88 fix(auth): logout POST-only con redirect a home:index, next seguro y STORAGES WhiteNoise
6e030e9 feat(home): landing v2 con contenido real, páginas institucionales y tests v3
e17f01c style(home): páginas institucionales con estética landing
b9cbbbb style(home): separador animado y espaciado en páginas institucionales
3993eae style(home): hero con colchón inferior para que la onda no tape el texto institucional
12d6eef style(home): cards con estampado de icono en quiénes somos
26259a2 style(home): separadores de sección variados en el landing
```

## Specs Synced

| Canonical | Action | Details |
|-----------|--------|---------|
| `openspec/specs/public-landing-page/spec.md` | **Created** (new capability) | full spec carried over verbatim: 5 requirements, 13 scenarios, 126 lines |
| `openspec/specs/tabler-core-vendor/spec.md` | Updated (composed) | 1 requirement MODIFIED in place (`SOCIALS-PLUGIN`), 4 unrelated requirements preserved byte-for-byte |

### Composition Method

The native composition command mandated by the `sdd-archive` skill is **unavailable in the
installed toolchain**, and was reproduced here:

```
$ gentle-ai sdd-archive-compose --help
Error: unknown command "sdd-archive-compose" — run 'gentle-ai help' for available commands
```

`gentle-ai 4.0.0` exposes only `review *`, `sync`, `install` and `skill-registry`. `gentle-ai sync`
ran and reported `1 files changed` (`opencode.jsonc`) without refreshing the dated skill, so the
skew persisted. No `openspec` binary exists on this machine either.

Composition therefore split into the two cases the project has already documented:

**Case A — `public-landing-page` had no canonical** (new capability). The delta file was copied
mechanically to a temp path, verified byte-identical with `diff -r` (**EMPTY**), and only then
promoted with `mv`. `sha256` of the source delta and of the promoted canonical are identical:
`baecc033a8ca4b90…`. This matches the precedent recorded in
`archive/2026-09-16-reesolicitar-servicio-activo/archive-report.md`
("native composition was not applicable because the canonical did not exist").

**Case B — `tabler-core-vendor` already had a canonical**. Deterministic `sed` range composition,
following `archive/2026-09-16-categoria-y-layout-servicios/archive-report.md`. No artifact byte ever
passed through a model Read/Write path. Every verification diff came back **EMPTY**:

| Check | Result |
|-------|--------|
| head, out `1–81` vs canonical `1–81` | EMPTY |
| MODIFIED `SOCIALS-PLUGIN`, out `82–119` vs delta `5–42` | EMPTY |
| preserved `NO-REGRESSION-GATE`, out `120–139` vs canonical `94–112` | EMPTY |

The three surviving requirements that did not change (`VENDORED-VERSION-PIN`, `NO-CDN-NO-BUILD`,
`UMD-EXPOSURE-CONTRACT`) are untouched; `SOCIALS-PLUGIN` went from 1 scenario to 4.

`rules.archive` from `openspec/config.yaml` ("Warn before merging destructive deltas") did **not**
trigger for this change: no requirement was removed, only one modified and one capability added.
No maintainer warning was required.

### Verification notes

- The `tabler-core-vendor` `SOCIALS-PLUGIN` delta contains the phrase
  `btn btn-icon btn-facebook` inside its own `(Previously: …)` annotation. A `grep` for the old
  footer markup therefore returns a legitimate 1, not 0 — the old markup itself is gone; the
  surviving match is the delta's historical note.
- `tabler-socials.min.css?v=151` appears exactly twice in the promoted spec (requirement body +
  scenario), as expected.

## Archive Contents

- `proposal.md` ✅ present
- `design.md` ✅ present
- `specs/public-landing-page/spec.md` ✅ present
- `specs/tabler-core-vendor/spec.md` ✅ present
- `tasks.md` ✅ present, 37/37 complete
- `verify-report.md` — absent (verification not run for this change)

Folder move readback: pre-move recursive snapshot vs archived tree → `diff -r` **EMPTY**.

## Source of Truth Updated

- `openspec/specs/public-landing-page/spec.md` (new)
- `openspec/specs/tabler-core-vendor/spec.md`

## Persistence

Filesystem write succeeded (see readbacks above). The Engram mirror
(`sdd/023-landing-page/archive-report`) was **not** persisted: the Engram server could not confirm
session registration during this session. Recorded as an outstanding mirror, not as a success.

## SDD Cycle Complete

The change is archived and both deltas are promoted. Implementation is merged in `main`.
Verification: **not run** (no `verify-report.md`); the change closed on 37/37 tasks plus the
`apps.home` test suite recorded in `tasks.md`. No unfinished tasks and no unresolved findings.
