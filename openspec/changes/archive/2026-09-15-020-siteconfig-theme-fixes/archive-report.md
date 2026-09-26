# Archive Report — 020-siteconfig-theme-fixes

**Change**: 020-siteconfig-theme-fixes
**Capability**: `020-siteconfig-theme-fixes` (delta over 019 `siteconfig-website` — Site Config & Theme Fixes)
**Archive date**: 2026-09-15
**Mode**: hybrid (openspec filesystem + Engram archive-report)

## Final-state facts

| Fact | Value | Source |
|------|-------|--------|
| Verify verdict | PASS (valid, no CRITICAL, 0 blockers) | `verify-report.md`, re-admitted by `gentle-ai sdd-verify-validate` at archive time |
| Requirements | 5/5 | `verify-report.md` (grep-verified 5 `### Requirement:` in promoted spec) |
| Scenarios | 7/7 | `verify-report.md` (grep-verified 7 `#### Scenario:` in promoted spec) |
| Tests | 228/228 (exit 0, `apps.core apps.user_auth`) | `verify-report.md` |
| Build | `manage.py check` clean; migrations dry-run clean | `verify-report.md` |
| Lint / JS | djlint clean, ruff clean, `node --check` on patched loader OK | `verify-report.md` |
| Tasks | 60/60 `[x]`, 0 unchecked | persisted `tasks.md` (Task Completion Gate) |
| Commits | `090c4c3` (feat: mantenimiento integrado a config del sitio y modal PDF público, 020/021) | repository log — later re-verification work (spec re-sync, remediation test `test_home_page_injects_model_theme_config_server_side`, +1 test) is present in the working tree as uncommitted edits to the archived spec/verify-report |

## Evidence revision resolution (no contradiction)

- Orchestrator launch prompt cites evidence_revision `sha256:82a0500607d1b4ea3641984f63f7d1e66fc22c1149be3c51b9cb1cadd7bb5aa4` — independently verified as the **sha256 of the `verify-report.md` file itself** at archive time.
- The YAML header inside `verify-report.md` declares `evidence_revision: sha256:ae17ba184490ade5c54f1b65f6141179adcf0baf17191e09eae840c35a8e1958` — the digest over proposal+spec+design+tasks (canonical concatenation), admitted by `sdd-verify-validate` (`valid: true, verdict: pass`) at archive time.
- These are two distinct fields (file hash vs artifact digest); both independently verified, no contradiction recorded.

## Verification snapshot (per `verify-report.md`)

- **5/5 requirements**: THEME-BASE-APPLIED, RESET-RESTORES-MODEL, THEME-CSS-PRIMARY-ONLY, SETTINGS-FORM-STANDARD, NO-REGRESSION-020.
- **7/7 scenarios** with covering tests executed at runtime (Django template/view tests + Node probe S1/S2/LOADER, 14/14 asserts on the real shipped JS).
- **No CRITICAL findings, 0 blockers.**

### Non-blocking warnings (from `verify-report.md`, recorded for audit)

1. **TDD documentary evidence**: apply-progress is narrative (Phases 1–4); Phases 5–7f only in inline `tasks.md` notes. Degraded CRITICAL→WARNING because substantive evidence is green (228/228, real test files, per-phase notes, new remediation test).
2. **Loader traceability**: the documented vendored patch (spec names Tabler 1.5.1, commit `c14686d`) was ported to the re-vendored 1.5.1 with light/dark-only behavior and an updated comment header — within the documented NO-REGRESSION-020 exception; the shipped file is 1.5.1 + patch, not the byte-exact binary of `c14686d`.

### Suggestions (from `verify-report.md`)

1. Fix misleading comment at `apps/core/tests/test_site_configuration_template.py:60`.
2. Remove the redundant `assertGreaterEqual(count, 1)` assertion in `test_logo_and_favicon_side_by_side`.

## Specs synced

| Domain | Action | Details |
|--------|--------|---------|
| `020-siteconfig-theme-fixes` | Created (main spec did not exist — delta IS the full spec) | `openspec/specs/020-siteconfig-theme-fixes/spec.md` — 5 requirements / 7 scenarios, h3 `### Requirement:` / h4 `#### Scenario:` standard matching canonical 007-tema-personalizado and tabler-core-vendor |

Mechanical copy via shell (`cp` → `diff -r` readback → `mv`); verbatim readback diff was empty (byte-identical promotion). No merge against a pre-existing main spec was required; no unrelated requirements were at risk of alteration.

## Archive contents

- `proposal.md` ✅
- `specs/020-siteconfig-theme-fixes/spec.md` ✅
- `design.md` ✅
- `tasks.md` ✅ (60/60 tasks complete)
- `verify-report.md` ✅
- `archive-report.md` ✅ (this file, additive)

Archive move performed as one shell transaction: pre-move recursive snapshot → `git mv` → mandatory `diff -r` snapshot-vs-destination readback (empty). Source directory confirmed absent from `openspec/changes/`.

## Source of truth updated

The following spec now reflects the new behavior (full capability spec promoted):
- `openspec/specs/020-siteconfig-theme-fixes/spec.md`

## Traceability (hybrid store)

Artifacts were read from filesystem paths (`openspec/changes/020-siteconfig-theme-fixes/…`, per the dispatcher's openspec locators); no Engram observation IDs were read for this archive. Native dispatcher status at archive time: `artifactStore: openspec`, `dependencies.archive: ready`, `nextRecommended: archive`, `applyState: all_done`, `blockedReasons: []`, `actionContext.mode: repo-local`.

## SDD Cycle Complete

The change has been fully planned, implemented, verified, and archived.
