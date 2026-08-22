```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:5555c66999b6f66cc5076074f3c46b11640c914cb33adb710f417fc61823dd46
verdict: pass
blockers: 0
critical_findings: 0
requirements: 5/5
scenarios: 10/10
test_command: python manage.py test
test_exit_code: 0
test_output_hash: sha256:9f378971311f405188585e0da434a15e8588f68d6a1139eb6bd62d2b32e8a973
build_command: python manage.py check
build_exit_code: 0
build_output_hash: sha256:1e3e63f221bde88816c4a4ef7367691607b20cc1d194028a02ec9ae0586cf9b1
```

## Verification Report

**Change**: 009-debug-toolbar
**Version**: spec 009-debug-toolbar (delta)
**Mode**: Standard (Strict TDD inactive)

### Completeness
| Metric | Value |
|--------|-------|
| Tasks total | 5 |
| Tasks complete | 5 |
| Tasks incomplete | 0 |

All tasks in `tasks.md` are checked (`[x]`): 1.1, 2.1, 3.1, 4.1, 5.1.

### Build & Tests Execution
**Build** (`python manage.py check`): ✅ Passed
```text
System check identified no issues (0 silenced).
```

**Tests** (`python manage.py test`): ✅ 341 passed / ❌ 0 failed / ⚠️ skipped (only the debug-toolbar test's explicit `skipTest` under `PRODUCTION=true`)
```text
Ran 341 tests in 93.946s
OK
Destroying test database for alias 'default'...
```
Targeted `apps.core.tests.test_debug_toolbar` runs:
- default env (DEBUG unset → False): 1 passed (asserts `debug_toolbar` NOT in `INSTALLED_APPS`)
- `DEBUG=True`: 1 passed (asserts `debug_toolbar` in `INSTALLED_APPS` and `DebugToolbarMiddleware` in `MIDDLEWARE`)
- `PRODUCTION=true`: 1 skipped (test skips instead of asserting absence)

**Coverage**: ➖ Not available (no coverage gate configured for this change).

### Spec Compliance Matrix
| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| DBG-1 | DEBUG=True & IS_PROD=False → toolbar in INSTALLED_APPS & MIDDLEWARE | `apps.core.tests.test_debug_toolbar > test_debug_toolbar_guard` (DEBUG=True run, OK) + harness | ✅ COMPLIANT |
| DBG-1 | IS_PRODUCTION=True → not present | verify-harness (runtime, `PRODUCTION=true`): INSTALLED_APPS/MIDDLEWARE absent, URL absent | ✅ COMPLIANT |
| DBG-1 | DEBUG=False → not in INSTALLED_APPS | `apps.core.tests.test_debug_toolbar` (default run, OK) | ✅ COMPLIANT |
| DBG-2 | active → INTERNAL_IPS contains `127.0.0.1` & `::1` | verify-harness (DEBUG=True): both present | ✅ COMPLIANT |
| DBG-3 | dev → `/__debug__/` route present | verify-harness (DEBUG=True): mount present + sub-routes resolve | ✅ COMPLIANT |
| DBG-3 | prod/no-debug → no `/__debug__/` route | verify-harness (PRODUCTION=true / DEBUG=False): mount absent | ✅ COMPLIANT |
| DBG-4 | requirements.txt absent debug-toolbar | static+runtime grep of `requirements.txt` | ✅ COMPLIANT |
| DBG-4 | no migrations/model/business-URL changes | `git show 6285061 --stat` (no migration files; only guarded settings/urls) | ✅ COMPLIANT |
| DBG-5 | `manage.py check` passes | `python manage.py check` (exit 0) | ✅ COMPLIANT |
| DBG-5 | test suite unaffected | `python manage.py test` (341 OK, exit 0) | ✅ COMPLIANT |

**Compliance summary**: 10/10 scenarios compliant.

### Correctness (Static Evidence)
| Requirement | Status | Notes |
|------------|--------|-------|
| DBG-1 | ✅ Implemented | `config/settings.py:123` guarded `if DEBUG and not IS_PRODUCTION:` appends `debug_toolbar` to `INSTALLED_APPS` and `debug_toolbar.middleware.DebugToolbarMiddleware` to `MIDDLEWARE`. |
| DBG-2 | ✅ Implemented | `config/settings.py:126` `INTERNAL_IPS = ['127.0.0.1', '::1']` inside the guard. |
| DBG-3 | ✅ Implemented | `config/urls.py:42` tightened to `if settings.DEBUG and not settings.IS_PRODUCTION:`; `config/urls.py:44` mounts `path('__debug__/', include('debug_toolbar.urls'))`. |
| DBG-4 | ✅ Implemented | `requirements-dev.txt:6` pins `django-debug-toolbar==4.4.2`; absent from runtime `requirements.txt`. No migrations. |
| DBG-5 | ✅ Implemented | `check` clean; full suite green. |

### Coherence (Design)
| Decision | Followed? | Notes |
|----------|-----------|-------|
| Guard `if DEBUG and not IS_PRODUCTION` in settings | ✅ Yes | `config/settings.py:123`. |
| `INTERNAL_IPS` set inside guard | ✅ Yes | `config/settings.py:126`. |
| URL mount under `if settings.DEBUG and not settings.IS_PRODUCTION` | ✅ Yes | `config/urls.py:42,44`. |
| Dependency only in `requirements-dev.txt`, not runtime | ✅ Yes | `requirements-dev.txt:6`; `requirements.txt` clean. |
| Placement "immediately after DEBUG definition (line 21)" | ⚠️ Deviation | Actual block at `config/settings.py:123` (after `MIDDLEWARE`), not line 21. Behavior identical; no spec impact. |

### Issues Found
**CRITICAL**: None

**WARNING**:
1. Design-coherence deviation — the guarded block was placed at `config/settings.py:123` (after the `MIDDLEWARE` list) rather than "immediately after the `DEBUG` definition (line 21)" as `design.md` states. Behavior is identical and no spec requirement is broken, but the design note is inaccurate and should be corrected or the code moved for traceability.
2. The committed test `apps.core.tests.test_debug_toolbar > test_debug_toolbar_guard` does NOT assert the production-inert guarantee: under `PRODUCTION=true` it calls `self.skipTest(...)` instead of asserting `debug_toolbar` is absent from `INSTALLED_APPS`/`MIDDLEWARE`. The fail-closed property (DBG-1 second scenario) is therefore not enforced by CI — it was proven only by independent runtime harness in this report.

**SUGGESTION**:
1. Strengthen the committed test to assert DBG-2 (`INTERNAL_IPS` contains `127.0.0.1` and `::1`) and DBG-3 (resolve `/__debug__/` sub-routes present in dev, absent in prod) so those scenarios are covered automatically by `python manage.py test`, not only by manual verification.
2. `config/settings.py:127` adds `DEBUG_TOOLBAR_CONFIG = {'IS_RUNNING_TESTS': False}`, which is not described in `design.md`/`spec.md`. It is harmless and useful (prevents toolbar interference during test runs); document it in the design for traceability.

### Verdict
PASS
Implementation matches all five DBG requirements and all ten scenarios at runtime (independently proven across dev/prod/debug-off modes); `manage.py check` is clean and the full 341-test suite is green. Two non-blocking items remain: a design-placement deviation and thin committed-test coverage of the fail-closed guarantee.
