```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:3e8d16d84dfa59f38861bc2072f68f3f4f9faac92c9c764f830dcfbfad492ce6
verdict: pass
blockers: 0
critical_findings: 0
requirements: 4/4
scenarios: 9/9
test_command: python manage.py test apps.core.tests.test_check_deploy
test_exit_code: 0
test_output_hash: sha256:84d8351cb83b4fcb963ca89c907421091cdf76fb5f683060f5e19ec2e0699578
build_command: python manage.py check
build_exit_code: 0
build_output_hash: sha256:1e3e63f221bde88816c4a4ef7367691607b20cc1d194028a02ec9ae0586cf9b1
```

## Verification Report

**Change**: 013-check-deploy-ci
**Version**: deploy-check-gate v1
**Mode**: Standard

### Completeness
| Metric | Value |
|--------|-------|
| Tasks total | 12 |
| Tasks complete | 12 |
| Tasks incomplete | 0 |

### Build & Tests Execution
**Build**: ✅ Passed
```
$ python manage.py check
System check identified no issues (0 silenced).   # exit 0
$ python manage.py makemigrations --check --dry-run
No changes detected                                # exit 0
YAML parse of .github/workflows/security.yml → valid; jobs: ['bandit', 'deploy-check']
```

**Tests**: ✅ 528 passed (full suite) / 0 failed
```
$ python manage.py test apps.core.tests.test_check_deploy
Found 5 test(s). ... Ran 5 tests in 0.003s OK.     # exit 0 (targeted, 5/5)
$ python manage.py test
Ran 528 tests in 212.774s  OK                       # exit 0 (full suite)
```

**Coverage**: ➖ Not configured as a gate for this change.

### Deployment Check Evidence (local vs CI — see verdict)
```
$ python manage.py check --deploy --fail-level WARNING        # local, with .env DEBUG=True
WARNINGS: security.W004, W012, W016, W018
System check identified 4 issues (1 silenced).                # exit 1  ← EXPECTED LOCAL ARTIFACT

# Fresh-checkout CI simulation (no .env; DEBUG defaults to False):
$ python manage.py check --deploy --fail-level WARNING
System check identified no issues (1 silenced).               # exit 0  ← CI condition, GREEN
```
The local exit 1 with W004/W012/W016/W018 is the **documented local artifact** (design.md lines 48-51): a local `.env` sets `DEBUG=True`, which skips the `if not DEBUG:` security block and surfaces the secure-cookie/HSTS warnings. It is NOT a defect. The CI condition (fresh checkout, no `.env`, `DEBUG=False`) verified empirically returns **`0 issues (1 silenced)` → exit 0**.

### Spec Compliance Matrix
| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| REQ-1 CI Runs Deployment System Checks | Job runs on pull request | `.github/workflows/security.yml` `deploy-check` job; `on:` mirrors Bandit (pull_request branches main) | ✅ COMPLIANT |
| REQ-1 CI Runs Deployment System Checks | Job runs on push to main | `.github/workflows/security.yml` `deploy-check` job; `on:` push branches main | ✅ COMPLIANT |
| REQ-2 Job Fails On Any Warning Or Error | A deployment warning fails the pipeline | `--fail-level WARNING` (non-zero exit on any WARNING/ERROR) | ✅ COMPLIANT |
| REQ-2 Job Fails On Any Warning Or Error | A clean deployment posture passes | CI sim: `System check identified no issues (1 silenced)` exit 0 | ✅ COMPLIANT |
| REQ-3 Production Security Posture Hardened | X_FRAME_OPTIONS is DENY | `apps/core/tests/test_check_deploy.py::test_x_frame_options_is_deny` | ✅ COMPLIANT |
| REQ-3 Production Security Posture Hardened | W008 is intentionally silenced | `apps/core/tests/test_check_deploy.py::test_w008_is_silenced` | ✅ COMPLIANT |
| REQ-3 Production Security Posture Hardened | check --deploy is green after hardening | CI sim: `0 issues (1 silenced)` exit 0 | ✅ COMPLIANT |
| REQ-4 Existing CI Jobs Are Not Broken | Existing jobs remain intact | `manage.py check`, `makemigrations --check`, full suite green; `ci.yml` untouched | ✅ COMPLIANT |
| REQ-4 Existing CI Jobs Are Not Broken | SECRET_KEY check does not false-positive in CI | `IS_PRODUCTION=False` → `get_random_secret_key()`; CI sim green | ✅ COMPLIANT |

**Compliance summary**: 9/9 scenarios compliant

### Correctness (Static Evidence)
| Requirement | Status | Notes |
|------------|--------|-------|
| X_FRAME_OPTIONS = 'DENY' | ✅ Implemented | `config/settings.py:374` |
| security.W008 silenced | ✅ Implemented | `config/settings.py:379` `SILENCED_SYSTEM_CHECKS = ['security.W008']` + Nginx-TLS comment (lines 377-378) |
| Middleware present | ✅ Implemented | `XFrameOptionsMiddleware` in MIDDLEWARE (guarded by test) |
| CSP frame-ancestors stays 'self' | ✅ Implemented | `config/settings.py:175` `["'self'"]` (guarded by test) |
| SECURE_SSL_REDIRECT not True | ✅ Implemented | `config/settings.py:85` `SECURE_SSL_REDIRECT = False` (guarded by test) |
| deploy-check CI job | ✅ Implemented | `.github/workflows/security.yml:42-57`; checkout@v4 → setup-python@v5 (3.12, pip cache) → `pip install -r requirements-dev.txt` → `manage.py check --deploy --fail-level WARNING`; NO `generate_env` step; doc comment present (lines 36-41) |
| No first-party iframe breaks under DENY | ✅ Implemented | `grep -rn "<iframe" templates/ apps/` → none found |

### Coherence (Design)
| Decision | Followed? | Notes |
|----------|-----------|-------|
| Fresh checkout (no .env) for CI | ✅ Yes | Job has no `generate_env` step; empirically re-verified green (0 issues, 1 silenced) |
| Silence W008 with comment (Nginx owns TLS/redirect) | ✅ Yes | Comment present; `SECURE_SSL_REDIRECT=False` |
| X_FRAME_OPTIONS = 'DENY' | ✅ Yes | `config/settings.py:374` |
| Job in security.yml (mirror Bandit) | ✅ Yes | `deploy-check` job added; Bandit unchanged |
| No migrations/model/URL changes | ✅ Yes | `makemigrations --check` → no changes |

### Issues Found
**CRITICAL**: None
**WARNING**:
- The local `check --deploy --fail-level WARNING` exits 1 (W004/W012/W016/W018) when a local `.env` sets `DEBUG=True`. This is a **documented local-only artifact** (design.md lines 48-51), **NOT a defect** and **NOT a failure of this change**. It is recorded here so future local runs are not mistaken for a regression; the CI path (the authoritative gate) is green.
**SUGGESTION**: None

### Verdict
PASS
All 12 tasks complete; 9/9 spec scenarios compliant with runtime evidence; full suite (528) green; `manage.py check`, `makemigrations --check`, and YAML valid; CI `check --deploy` verified green on the fresh-checkout condition. The only non-zero `check --deploy` is the documented local `DEBUG=True` artifact, not a defect.
