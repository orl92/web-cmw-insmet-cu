# Archive Report — tabler-151-upgrade

**Change**: tabler-151-upgrade
**Archived to**: `openspec/changes/archive/2026-09-14-tabler-151-upgrade/`
**Date**: 2026-09-14
**Artifact store mode**: hybrid (filesystem + Engram)
**Phase**: sdd-archive
**Intentional override**: none — full archive; no partial archive, no stale-checkbox reconciliation.

## Final State (at close)

- **Verdict**: **PASS** — all 8 requirements / 15 scenarios compliant (14/14 contract tests, 444/444 affected-app suite `apps.core apps.meteo apps.home`, `manage.py check` clean, browser smoke re-run independently).
- **Tasks**: 16/16 `[x]`; zero unchecked implementation tasks in the persisted artifact.
- **Post-verify correction**: commit `be43bb2` ("fix(tabler): escala iconos JS con --tblr-icon-size y amplía contrato a .js (change 151)") fixed the icon-scaling finding left by `sdd-verify`: `static/dist/js/maps.js` (3x24), `static/dist/js/utils.js` (4x24) and `static/dist/js/map_station.js` (3x44) now scale via `--tblr-icon-size` instead of `font-size:`; `test_webfont_icons_scaled_via_icon_size_variable_not_font_size` was extended to scan non-min project `.js` under `static/dist/js/`. Re-verified: 14/14 contract + 444/444 suite + `check` clean. Tasks.md entry 4.6 documents the correction.
- **HEAD**: `be43bb2`. Foreign commit `811304e` ("proxy satelite off") is present and unrelated to this change (ops note: `home` logs a handled "Error al cargar estaciones" console.error from `map_station.js`, untouched by this change).

## Specs Synced (source of truth)

| Domain | Action | Details |
|--------|--------|---------|
| 007-tema-personalizado | Updated (composed) | 11 requirements preserved byte-for-byte + 3 ADDED (LIGHT-DEFAULT-EXPLICIT, THEME-LOADER-151, THEME-BASE-020-VERIFIED) = 14 requirements / 21 scenarios |
| tabler-core-vendor | Already promoted — validated | Byte-identical to delta (sha256 `c588efbd…5d633` both); NOT re-written or re-promoted per launch instruction |

### Composition evidence (007)

```bash
gentle-ai sdd-archive-compose \
  --canonical "openspec/specs/007-tema-personalizado/spec.md" \
  --delta "openspec/changes/tabler-151-upgrade/specs/007-tema-personalizado/spec.md" \
  --output "openspec/specs/007-tema-personalizado/spec.md.compose-tmp" \
&& mv "openspec/specs/007-tema-personalizado/spec.md.compose-tmp" "openspec/specs/007-tema-personalizado/spec.md"
```

Exit 0. Verified: canonical now has 14 `### Requirement:` / 21 `#### Scenario:`; no `.compose-tmp` residue; pre-existing requirements preserved in order, ADDED block appended at end. The prior blocking issue (h2 legacy headings) was resolved before this relaunch by normalizing the canonical to `### Requirement:` / `#### Scenario:` (content unchanged), so composition succeeded on the first attempt of this run.

## Mechanical Copy Readbacks (verbatim)

1. Step 3 archive move, `diff -r snapshot vs destination`: **empty (exit 0)** — byte-identity confirmed (archived tree == pre-move recursive snapshot; archive-report additive-only, excluded from comparison).
2. Step 2 tabler-core-vendor validation, `diff -r delta vs canonical`: **empty (exit 0)** — byte-identity confirmed (sha256 `c588efbd274e92ef00874eefb2621eeac8d0aaf8a8b2d72938cc55aad8b5d633` on both files).

## Artifacts Read (traceability)

Hybrid store — locators were filesystem paths; all read in full:

- `openspec/changes/tabler-151-upgrade/proposal.md`
- `openspec/changes/tabler-151-upgrade/design.md`
- `openspec/changes/tabler-151-upgrade/tasks.md`
- `openspec/changes/tabler-151-upgrade/verify-report.md`
- `openspec/changes/tabler-151-upgrade/specs/007-tema-personalizado/spec.md`
- `openspec/changes/tabler-151-upgrade/specs/tabler-core-vendor/spec.md`

## Verification Findings (final, per Final-State Authority)

Higher-ranked sources (persisted tasks artifact 16/16, launch-prompt final-state facts, commit `be43bb2`) outrank intermediate `verify-report`/`apply-progress` snapshot claims. `verify-report` was updated to PASS before this relaunch and carries **zero CRITICAL findings, zero blockers** — no archive-blocking condition exists.

- WARNING #1 (maps.js toast icons `font-size` anti-pattern): **RESOLVED** — fixed in commit `be43bb2` (maps.js, utils.js, map_station.js use `--tblr-icon-size`; contract test extended to non-min `.js`); re-verified 14/14 + 444/444.
- WARNING #2 (apply-progress artifact absent): procedural, orchestrator-documented (apply ended `all_done`); TDD substance independently reconstructed from tasks.md inline RED/GREEN notes, git history and live execution. Recorded as procedural note, not a defect.
- SUGGESTION #1 (extend icon-scaling contract to `.js`): **DONE** in `be43bb2`.
- SUGGESTION #2 (home "Error al cargar estaciones"): ops note only — satellites proxy disabled by unrelated commit `811304e`; not a regression of this change.
- SUGGESTION #3 (HEAD mismatch vs handoff): superseded — actual HEAD is `be43bb2` (final-state fact); `811304e` remains the foreign commit in history.

## Archive Verification (Step 4)

- [x] Main specs updated correctly (007 composed; tabler-core-vendor validated byte-identical)
- [x] Change folder moved to `openspec/changes/archive/2026-09-14-tabler-151-upgrade/` via `git mv` (6 files renamed, staged)
- [x] Archive contains all artifacts: proposal.md, specs/007-tema-personalizado/spec.md, specs/tabler-core-vendor/spec.md, design.md, tasks.md, verify-report.md
- [x] Archived tasks.md: 16/16 `[x]`, 0 unchecked implementation tasks
- [x] Active changes directory no longer contains this change
- [x] Verbatim `diff -r` readbacks empty (only passing evidence)

## Engram Persistence

- Observation `sdd/tabler-151-upgrade/archive-report` persisted via `mem_save` (topic_key, type architecture, capture_prompt false) — Engram observation id **308**, sync_id `obs-befef76c43af59e3`.
