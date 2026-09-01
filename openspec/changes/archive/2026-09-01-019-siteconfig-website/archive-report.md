# Archive Report — 019-siteconfig-website

**Change**: 019-siteconfig-website
**Capability**: `tema-personalizado` (extended: web-managed SiteConfiguration + model-authoritative site color)
**Archive date**: 2026-09-01
**Mode**: openspec

## What shipped

5 new requirements appended to `openspec/specs/007-tema-personalizado/spec.md`:

1. **SITECONFIG-EDIT-PAGE** — Dashboard web UI for editing the `SiteConfiguration` singleton (primary color, theme base, brand logo, favicon), mirroring `CompanySettingsUpdateView` pattern. Includes permission-gated form, hex validation, multipart file handling, and singleton row persistence via `site_branding` context processor.

2. **PRIMARY-COLOR-AUTHORITATIVE** — Model default changed from `#0b6e99` to `#2b4b9b`. Existing singleton row updated via reversible `RunPython` data migration (`core.0002`, gitignored). `scripts.html` applies the model hex as inline CSS variables on fresh load; reset handler clears localStorage and re-applies model hex. Named Tabler swatches remain visitor-local overrides.

3. **THEME-CSS-RECONCILED** — Removed obsolete `--tblr-primary: #0b6e99` and green `--tblr-secondary` values from `theme.css`. Dark mode tuned to `#2b4b9b`. `tabler.min.css` / `tabler-themes.min.css` untouched.

4. **LOGO-FIXED** — `logo.html` and `logo.svg` confirmed unmodified. Dark mode handled by `navbar-brand-autodark`. `brand_logo.url` rendering preserved per existing LOGO requirement.

5. **NO-REGRESSION-019** — Enhanced regression gate: runtime theme switcher, Tabler components, and `site_branding` context processor not regressed. `check`, `test apps.core` (132 OK), and `djlint` all pass.

## Final-state facts (source of truth: orchestrator launch prompt, rank 3)

| Fact | Value | Source |
|------|-------|--------|
| Verify verdict | PASS WITH WARNINGS | Orchestrator final-state handoff |
| Requirements | 5/5 | Orchestrator final-state handoff |
| Scenarios | 8/8 | Orchestrator final-state handoff |
| Tests | 132 OK, 0 failed | Orchestrator final-state handoff |
| Build | check clean | Orchestrator final-state handoff |
| Lint | djlint clean, ruff clean | Orchestrator final-state handoff |
| Commits | `524e7b6` (feat), `b9f6e68` (fix), `70036ef` (style) | Orchestrator final-state handoff |

## Verification snapshot

Per `verify-report.md` (admitted by `gentle-ai sdd-verify-validate`, `valid: true, verdict: pass_with_warnings`):

- **5/5 requirements** implemented and verified (SITECONFIG-EDIT-PAGE, PRIMARY-COLOR-AUTHORITATIVE, THEME-CSS-RECONCILED, LOGO-FIXED, NO-REGRESSION).
- **8/8 scenarios** verified with runtime and/or static evidence.
- **13 site-config tests** new; full 132-suite passes.
- **No CRITICAL findings.** 0 blockers.

### Warnings (non-blocking)

1. **Absent `apply-progress` TDD-evidence artifact.** Implemented via direct commits, not `sdd-apply` phase. TDD was demonstrably followed (RED-first tasks 1.1/2.1/2.4; test files committed and passing). Evidence lives in the repository tests.
2. **Automated JS DOM behavior not exercisable.** Swatch pick and "Restablecer" reset are client-side DOM behavior. Project has no browser/JS test harness (no Node, no bundler). Verified by source inspection of `scripts.html` and `hexToRgb` math. Residual risk recorded below.

### Suggestions for future work

1. Add a static regression assertion for `THEME-CSS-RECONCILED` (e.g. a test asserting `theme.css` does not contain `#0b6e99` or green secondaries).
2. If a browser harness is ever introduced, add a DOM test covering fresh-visitor seed, named-swatch selection, and reset-to-model paths.

## Final-state deviations/notes from orchestrator handoff

1. **12 named→hex swatch values** in `scripts.html` confirmed to exactly match `tabler-themes.min.css` presets (closes design.md open question).
2. **Hex→CSS rendering** applied as inline `--tblr-primary`/`--tblr-primary-rgb` on `document.documentElement` (vanilla JS, no bundler). Model `#2b4b9b` renders on fresh load and after reset.
3. **Residual manual risk**: automated JS DOM behavior (swatch pick / reset) not exercisable without a browser harness. Recorded as SUGGESTION for future manual/browser smoke check.
4. **`logo.html`/`logo.svg` confirmed unmodified**; dark mode handled by `navbar-brand-autodark`.
5. **Migration `core.0002`** (gitignored) changed default `#0b6e99 → #2b4b9b` and updated the existing singleton row via RunPython (reversible).

## Task completion

23/23 tasks complete — all implementation, verification, and review tasks checked `[x]` in the persisted `tasks.md`.

## Archive contents

- `proposal.md` ✅
- `specs/019-siteconfig-website/spec.md` ✅
- `design.md` ✅
- `tasks.md` ✅
- `verify-report.md` ✅
- `archive-report.md` ✅ (this file)

## Source of truth updated

Delta requirements merged into `openspec/specs/007-tema-personalizado/spec.md`:
- SITECONFIG-EDIT-PAGE (added)
- PRIMARY-COLOR-AUTHORITATIVE (added)
- THEME-CSS-RECONCILED (added)
- LOGO-FIXED (added)
- NO-REGRESSION-019 (added — distinct from existing NO-REGRESSION)

All 6 pre-existing 007 requirements preserved unchanged (BRAND-CSS-OVERRIDE, DARK-MODE-BRAND, PER-INSTANCE-CONFIG, FAVICON, LOGO, NO-REGRESSION).

## SDD Cycle Complete

The change has been fully planned, implemented, verified, and archived.
