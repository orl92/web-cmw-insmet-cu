```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:dfc4e8538ff3a4869c6c0346fa61cb363fa657bd78777095df1d195c373503ab
verdict: pass_with_warnings
blockers: 0
critical_findings: 0
requirements: 6/6
scenarios: 7/7
test_command: source .venv/bin/activate && python manage.py test
test_exit_code: 0
test_output_hash: sha256:dfc4e8538ff3a4869c6c0346fa61cb363fa657bd78777095df1d195c373503ab
build_command: source .venv/bin/activate && python manage.py check
build_exit_code: 0
build_output_hash: sha256:1e3e63f221bde88816c4a4ef7367691607b20cc1d194028a02ec9ae0586cf9b1
```

## Verification Report

**Change**: 007-tema-personalizado
**Version**: N/A (delta spec, capability `tema-personalizado`)
**Mode**: Standard

### Completeness
| Metric | Value |
|--------|-------|
| Tasks total | 18 |
| Tasks complete | 18 |
| Tasks incomplete | 0 |

### Build & Tests Execution
**Build**: ✅ Passed
```text
$ python manage.py check
System check identified no issues (0 silenced).
exit 0
$ python manage.py makemigrations --check --dry-run
No changes detected
exit 0
```

**Tests**: ✅ 481 passed / ❌ 0 failed / ⚠️ 0 skipped (full suite)
```text
$ python manage.py test
Ran 481 tests in 151.717s
OK
exit 0
New change tests: apps.core.tests.test_site_branding_context_processor (2),
apps.core.tests.test_site_configuration_branding (2) — 4 tests, all OK.
```

**Coverage**: Not available (project has no coverage threshold configured) — compliance is proven via runtime test evidence plus djlint/ruff static checks per the established UI verification standard.

### Spec Compliance Matrix
| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| BRAND-CSS-OVERRIDE | Global palette applied | structural: `theme.css` `:root` overrides; linked after tabler in head.html | ✅ COMPLIANT |
| BRAND-CSS-OVERRIDE | No Tabler fork | `git diff` — no `static/dist/css/tabler*.css` changed | ✅ COMPLIANT |
| DARK-MODE-BRAND | Brand-aware dark mode | structural: `[data-bs-theme="dark"]` block in theme.css | ✅ COMPLIANT |
| PER-INSTANCE-CONFIG | Instance re-theme without code | `test_site_branding_context_processor.py` + `test_site_configuration_branding.py` | ✅ COMPLIANT |
| FAVICON | Favicon rendered | structural: `static/dist/img/favicon.ico` present + conditional `href` in head.html | ✅ COMPLIANT |
| LOGO | Default brand mark | structural: `logo.html` inline SVG fallback; navbar + sidebar include | ✅ COMPLIANT |
| LOGO | Overridden brand mark | structural: `logo.html` renders `brand_logo.url` when present | ✅ COMPLIANT |

**Compliance summary**: 7/7 scenarios compliant. Backend/model scenarios (PER-INSTANCE-CONFIG unit tests) proven by passing Django runtime tests; UI/theme scenarios verified by template-structure inspection + djlint per the project's UI verification standard (JS runtime test runners are hard-prohibited — no Node/bundlers).

### Correctness (Static Evidence)
| Requirement | Status | Notes |
|------------|--------|-------|
| BRAND-CSS-OVERRIDE | ✅ Implemented | `theme.css` re-declares primary, primary-rgb, link, secondary (ocean-blue/coastal-green); linked after `tabler.min.css` in `head.html:17`; Tabler source untouched |
| DARK-MODE-BRAND | ✅ Implemented | `[data-bs-theme="dark"]` block with brand-tuned dark variables |
| PER-INSTANCE-CONFIG | ✅ Implemented | `primary_color`/`theme_base`/`brand_logo`/`favicon` on `SiteConfiguration`; `FileHandlerMixin` + `file_fields=['brand_logo','favicon']`; `default_permissions=()` + 4 Spanish perms; `site_branding` registered in settings; `themeConfig` seeded from context processor (not hard-coded) |
| FAVICON | ✅ Implemented | `favicon.ico` asset tracked at `static/dist/img/favicon.ico`; conditional `{{ site_branding.favicon.url }}` in head.html |
| LOGO | ⚠️ Partial (design deviation) | navbar + sidebar reuse `logo.html` (conditional brand_logo). Footer brand-logo reuse intentionally SKIPPED — footer keeps alliance images only (CITMA/AMA/INSMET). Deviates from design's `<home/footer.html>` target but does not break any LOGO scenario requirement (the two LOGO scenarios are navbar/sidebar brand mark; footer is not a LOGO scenario) |
| NO-REGRESSION | ✅ Implemented | `check` clean, full suite 481 green, djlint + ruff clean; theme switcher (`settings.html`/`scripts.html`) logic preserved |

### Coherence (Design)
| Decision | Followed? | Notes |
|----------|-----------|-------|
| theme.css loaded after tabler.min.css | ✅ Yes | `head.html:17` after `tabler.min.css:16` |
| SiteConfiguration branding fields + FileHandlerMixin | ✅ Yes | correct fields, mixin, file_fields, perms |
| site_branding context processor registered | ✅ Yes | `settings.py:182`; request-scoped reuse of middleware fetch |
| themeConfig seeded from context processor | ✅ Yes | `scripts.html:12-14` uses `site_branding.*` |
| favicon conditional href | ✅ Yes | `head.html:6-14` |
| logo reuse in navbar/sidebar/footer | ⚠️ Partial | navbar + sidebar done via `logo.html`; footer SKIPPED (alliance images only) — documented deviation, non-breaking |
| No Tabler fork | ✅ Yes | no `tabler*.css` modified |

### Issues Found
**CRITICAL**: None
**WARNING**:
- Footer brand-logo reuse intentionally skipped (design target `<home/footer.html:70-86>` not met). Footer keeps alliance images (CITMA/AMA/INSMET) only. This is a documented, deliberate deviation that does NOT break any spec requirement (the LOGO scenarios target navbar/sidebar brand mark; footer is not a LOGO scenario), so it is non-blocking. If the footer should also honor `brand_logo`, add it in a follow-up.
- Theme switcher radio highlight: `scripts.html` seeds `theme-primary` with a custom hex (`{{ site_branding.primary_color }}`, e.g. `#0b6e99`), but the offcanvas settings radios present discrete named theme-primary presets (blue/green/red/etc.). A custom hex value will not match any radio, so no radio highlights when a custom primary is active. The switcher still works functionally (it reads `themeConfig` and applies `data-bs-theme-*`); only the selected-state highlight is off. This is a UX nuance, not a spec break (NO-REGRESSION preserves switcher behavior; PER-INSTANCE-CONFIG seeds the config). Non-blocking.

**SUGGESTION**:
- Consider a later enhancement: unify the per-instance `primary_color` with the runtime switcher's radio set (e.g. add a "Custom" option or extend the preset list) so the active custom primary highlights in the settings panel.

### Baselines (pre-existing, non-blocking, NOT introduced by this change)
- `RuntimeWarning: DateTimeField Warning.valid_until received a naive datetime` — pre-existing in other test suites, unrelated to this change.

### Verdict
PASS WITH WARNINGS
All 6 requirements and 7 scenarios met; full suite (481) green, check/makemigrations/djlint/ruff clean. Two non-blocking warnings (footer logo skip — documented intent; custom-primary radio highlight — UX nuance), neither breaking a spec requirement.
