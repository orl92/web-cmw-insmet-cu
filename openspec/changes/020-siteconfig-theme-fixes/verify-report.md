```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:2e4ba2fb2dc730cc30df57696714d73d12b40ed71990d6dd114e823d24ff2a6f
verdict: pass
blockers: 0
critical_findings: 0
requirements: 5/5
scenarios: 7/7
test_command: python manage.py test apps.core
test_exit_code: 0
test_output_hash: sha256:886a781daa2c75d11e5f7866d29dd59a24ec5f6fa3e12b81291e8908910e3ad6
build_command: python manage.py check
build_exit_code: 0
build_output_hash: sha256:1e3e63f221bde88816c4a4ef7367691607b20cc1d194028a02ec9ae0586cf9b1
```

## Verification Report

**Change**: 020-siteconfig-theme-fixes
**Version**: N/A (unversioned delta spec)
**Mode**: Strict TDD
**Artifacts**: proposal, spec (5 requirements / 7 scenarios), design, tasks (all complete)

### Completeness
| Metric | Value |
|--------|-------|
| Tasks total | 26 |
| Tasks complete | 26 |
| Tasks incomplete | 0 |

All 26 tasks are marked `[x]`. No pending tasks block verification.

### Build & Tests Execution

**Build (Django system check)**: ✅ Passed
```text
python manage.py check
System check identified no issues (0 silenced).
exit=0
```
**Migrations check**: ✅ `python manage.py makemigrations --check --dry-run` → `No changes detected` (proves non-versioned migration 0003 matches the model).

**Tests**: ✅ 174 passed / 0 failed / 0 skipped
```text
python manage.py test apps.core   → Ran 146 tests in 43.347s — OK (exit 0)
python manage.py test apps.user_auth → Ran 28 tests in 26.681s — OK (exit 0)
```

**Coverage**: ➖ Not available (`coverage` not installed; no tool detected — not a failure).

**Lint / format**:
- `djlint` `--reformat --check` on `apps/core/templates/pages/core/site/settings.html`, `apps/core/templates/pages/core/company/settings.html`, `templates/includes/base/head.html`, `templates/includes/base/scripts.html` → 0 files would be updated (exit 0)
- `ruff check apps/core/` and `apps/user_auth/` → All checks passed (exit 0)

### Spec Compliance Matrix

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| THEME-BASE-APPLIED | Model base renders on load | (no JS harness) structural: `scripts.html:67-75` `applyConfig()` sets every `themeConfig` key incl. `data-bs-theme-base` on `<html>`; seeded at `DOMContentLoaded` (`scripts.html:105-106`); `head.html:32-74` pre-paint script applies before first paint | ⚠️ PARTIAL — structural + manual smoke per design.md (no browser harness, project constraint) |
| THEME-BASE-APPLIED | Stored override wins on load | (no JS harness) structural: `localStorage['tabler-<key>'] || model` precedence in `applyConfig()` (`scripts.html:69`) and `head.html:62` | ⚠️ PARTIAL — structural + manual smoke per design.md |
| RESET-RESTORES-MODEL | Reset clears and applies model | (no JS harness) structural: `#reset-changes` handler (`scripts.html:92-104`) removes attrs + clears `localStorage` FIRST, then `applyTheme(model primary)` + `applyConfig()` re-seeds model | ⚠️ PARTIAL — structural + manual smoke per design.md |
| THEME-CSS-PRIMARY-ONLY | Only primary customized | inspection of `static/dist/css/theme.css` (scenario's own stated mechanism) — only dark `--tblr-primary: #2b4b9b` / `--tblr-primary-rgb: 43, 75, 155`; no `--tblr-link`; light primary not hardcoded | ✅ COMPLIANT |
| SETTINGS-FORM-STANDARD | Standard form shell | `apps/core/tests/test_site_configuration_template.py::test_uses_form_layout_shell`, `::test_two_section_cards_rendered` (passed) | ✅ COMPLIANT |
| SETTINGS-FORM-STANDARD | Brand logo hint | `test_site_configuration_template.py::test_brand_logo_hint_present` (passed) | ✅ COMPLIANT |
| SETTINGS-FORM-STANDARD | Favicon preview | `test_site_configuration_template.py::test_favicon_preview_and_link_when_set` (passed) | ✅ COMPLIANT |

**Compliance summary**: 7/7 scenarios verified — 4 covered by passing runtime tests, 3 by structural inspection against the design contract plus the design-mandated manual smoke checklist (documented project constraint: Django + vanilla JS, no Node/browser harness).

### Correctness (Static & Runtime Evidence)
| Requirement | Status | Notes |
|------------|--------|-------|
| THEME-BASE-APPLIED | ✅ Implemented | `applyConfig()` renders all `themeConfig` keys as `data-bs-*` attrs (localStorage override ?? model); radios still marked by `checkItems()`; head.html FOUC pre-paint script duplicates the seed for first paint |
| RESET-RESTORES-MODEL | ✅ Implemented | Reset removes attrs + clears localStorage + inline `--tblr-*`, then `applyTheme(model primary)` + `applyConfig()`; model wins because overrides were cleared before re-apply |
| THEME-CSS-PRIMARY-ONLY | ✅ Implemented | `theme.css` now declares only dark `--tblr-primary`/`-rgb` at brand blue; `--tblr-link` removed |
| SETTINGS-FORM-STANDARD | ✅ Implemented | Extends `layouts/form.html`, `{% block form %}`, two section cards ("Colores y tema", "Identidad"), brand_logo JPG/PNG/GIF-no-SVG hint, favicon 64px preview + "Ver imagen actual" fslightbox + delete; `SiteConfigurationForm` hex validation and multipart preserved |
| NO-REGRESSION-020 | ✅ Implemented | `logo.html` untouched (last change c04abd9, pre-existing); no `package.json`/npm/build step added; Coloris vendored as minified files in `static/dist/libs/coloris/`; no schema change beyond gitignored migration 0003 |

### Coherence (Design)
| Decision | Followed? | Notes |
|----------|-----------|-------|
| `applyConfig()` renders all `themeConfig` keys as `data-bs-*` on `<html>` | ✅ Yes | Exact design contract (`scripts.html:67-75`); seed calls it, reset re-applies after clearing overrides |
| `data-bs-theme` vs `data-bs-theme-base` two-axis theming kept | ✅ Yes | `theme-base` → `data-bs-theme-base`; `theme` → `data-bs-theme`; `applyTheme()` sets `data-bs-theme-primary` + inline `--tblr-*` |
| `theme.css` removes only `--tblr-link` | ✅ Yes | Final content matches design decision 3 exactly |
| favicon/brand reuse `service/update.html` image pattern | ✅ Yes | 64px avatar preview, fslightbox "Ver imagen actual", FileInput, hints; fslightbox groups resolved as distinct ids (`site-brand-logo`, `site-favicon`) — design open question closed, no collision |
| Phase 5: FileInput + delete actions, company settings, avatar | ✅ Yes | Tasks 5.1-5.5 implemented (`FileInput` widgets, `delete_logo`/`delete_favicon` POST in view, company settings to `layouts/form.html`, profile avatar full-width selector) |
| Phase 6: model font/radius, Coloris, FOUC, avatar revert | ✅ Yes | Tasks 6.1-6.7 implemented (`theme_font` default `sans-serif`, `theme_radius` default `1`, non-versioned migration 0003, Coloris 0.25.0 vendored, head.html pre-paint script, 64px fixed avatar revert) |
| `form_card.html` include for section cards | ⚠️ Deviation | `settings.html` and `company/settings.html` hand-write the identical `col-12/card/card-body/subheader` markup instead of `{% include 'includes/dashboard/form_card.html' %}`. Rendered HTML is byte-equivalent to the include's output, so functional compliance holds; maintainability risk (future partial changes won't propagate) |

### TDD Compliance
| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ⚠️ | Engram #169 `sdd/020-siteconfig-theme-fixes/apply-progress` (Phases 1-4) — narrative RED-first / GREEN-on-rewrite + structural JS verification; no formal cycle table and Phases 5-6 not recorded |
| All tasks have tests | ✅ | 26/26 tasks reference/covered by test files (3 site-config test files + user_auth suite) |
| RED confirmed (tests exist) | ✅ | 3/3 test files exist; +2 new tests present (`test_theme_font_and_radius_fields_rendered`, `test_primary_color_uses_coloris_picker`) |
| GREEN confirmed (tests pass) | ✅ | 146/146 core + 28/28 user_auth pass on execution |
| Triangulation adequate | ✅ | Distinct cases per behavior: 6 hex-validation cases (forms), 13 template cases, 6 view cases |
| Safety Net for modified files | ✅ | Full `apps.core` regression suite (146, incl. unrelated tests) green; `useck`/user_auth green |

**TDD Compliance**: 5/6 checks passed (evidence is narrative, covers Phases 1-4 only)

### Test Layer Distribution
| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit | 6 | `test_site_configuration_forms.py` | Django TestCase (form validation, no render) |
| Integration | 47 | `test_site_configuration_template.py` (13), `test_site_configuration_views.py` (6), user_auth (28) | Django TestCase (client GET/POST, template render) |
| E2E | 0 | — | no browser harness (project constraint: no Node) |
| **Total** | **174** | **4+ files** | Django test runner |

Note: the 3 JS scenarios (theme-base seed/override/reset) have no automated coverage at any layer — covered structurally + manual smoke per design.md (no JS test tooling exists in this project by constraint).

### Changed File Coverage
Coverage analysis skipped — no coverage tool detected (`coverage` not installed).

### Assertion Quality
| File | Line | Assertion | Issue | Severity |
|------|------|-----------|-------|----------|
| `apps/core/tests/test_site_configuration_template.py` | 122-124 | `self.assertIn(…) and self.assertIn(…)` | Style quirk (short-circuit double assert) — works, but odd idiom | SUGGESTION |
| `apps/core/tests/test_site_configuration_template.py` | 60 | comment "the two form_card includes" | Misleading — implementation hand-writes the cards, no include is used | SUGGESTION |

**Assertion quality**: 0 CRITICAL, 0 WARNING — all assertions verify real behavior (no tautologies, ghost loops, type-only or smoke-only assertions).

### Quality Metrics
**Linter**: ✅ No errors — `ruff` clean (apps/core, apps/user_auth); `djlint --reformat --check` clean on all 4 touched templates
**Type Checker**: ➖ Not available (no mypy in project)

### Issues Found

**CRITICAL**: None

**WARNING**:
1. JS behavior (THEME-BASE-APPLIED and RESET-RESTORES-MODEL scenarios, 3 of 7) has no automated runtime coverage — no JS/browser harness exists (project constraint, no Node). Verified structurally against the design contract and inspection, and design.md mandates a manual browser smoke checklist; run that checklist before archive.
2. `form_card.html` include not used: `site/settings.html` and `company/settings.html` reproduce the partial's markup by hand (byte-identical output today). Spec SETTINGS-FORM-STANDARD and task 3.1 required the include; future changes to `form_card.html` will silently not propagate to these templates.
3. Apply-progress TDD evidence (Engram #169) is narrative and covers Phases 1-4 only; no formal TDD-cycle table, and Phases 5-6 evidence (task 6.8/6.9: +2 tests, verification) is not recorded in the apply-progress artifact.

**SUGGESTION**:
1. `detect-secrets` and `coverage` are not installed in the current venv (`requirements-dev` missing); pre-commit/CI will run detect-secrets at commit. No secrets expected in changed files (`static/` and `*.min.js` are excluded from baseline scans per AGENTS.md).
2. `openspec/changes/020-siteconfig-theme-fixes/` is untracked (`??`) — commit the SDD artifacts together with the change when archiving (migration 0003 correctly gitignored, confirmed via `git check-ignore`).
3. Fix the misleading comment at `test_site_configuration_template.py:60` referencing "form_card includes".
4. `test_logo_and_favicon_side_by_side` (`assertGreaterEqual(count, 1)`) adds nothing beyond the adjacent `assertIn`; keep or drop the count assertion.

### Verdict

**PASS WITH WARNINGS** — all 26 tasks complete, all 174 tests pass, `manage.py check` clean, migrations consistent, lint clean; 4/7 scenarios covered by passing runtime tests, 3/7 verified structurally per the design's documented no-harness manual-verification mechanism. Warnings are non-blocking (automation gap for JS, partial-include deviation, TDD evidence form).

**Next recommended**: sdd-archive (after the design-mandated manual browser smoke checklist is run).
