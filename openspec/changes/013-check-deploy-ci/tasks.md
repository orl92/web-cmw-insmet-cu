# Tasks: Add `manage.py check --deploy` Gate to CI

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~40 (settings + workflow + 1 test module) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

## Phase 1: Settings Hardening (`config/settings.py`)

- [ ] 1.1 Change `X_FRAME_OPTIONS = 'SAMEORIGIN'` to `X_FRAME_OPTIONS = 'DENY'` (line 288). Resolves W019 for real.
- [ ] 1.2 Add `SILENCED_SYSTEM_CHECKS = ['security.W008']` with a comment explaining Nginx terminates TLS and performs the HTTPS redirect, so Django intentionally does not set `SECURE_SSL_REDIRECT = True`.
- [ ] 1.3 Verify no first-party view is embedded in an `<iframe>` that would break under `DENY` (grep templates for `iframe`; check admin/any embedding). If a legitimate framing need exists, scope per-view instead of reverting.

## Phase 2: CI Job (`.github/workflows/security.yml`)

- [ ] 2.1 Add a `deploy-check` job that triggers on `pull_request` + `push` to `main` (mirror the existing Bandit job's `on:`).
- [ ] 2.2 Steps: `actions/checkout@v4`, `actions/setup-python@v5` (3.12, pip cache), `pip install -r requirements-dev.txt`, then `python manage.py check --deploy --fail-level WARNING`.
- [ ] 2.3 Confirm the job runs on a fresh checkout with **no `.env`** (do NOT run `generate_env`; `DEBUG` defaults to `False` so the security block is active and no DB connection is opened).

## Phase 3: Tests (strict_tdd)

- [ ] 3.1 Add a settings/contract test asserting `settings.X_FRAME_OPTIONS == 'DENY'`.
- [ ] 3.2 Add a test asserting `'security.W008' in settings.SILENCED_SYSTEM_CHECKS`.
- [ ] 3.3 (Manual/CI) Document expected `check --deploy --fail-level WARNING` output on a fresh checkout: `0 issues (1 silenced)` → exit 0.

## Phase 4: Verification

- [ ] 4.1 On a fresh checkout (no `.env`): `python manage.py check --deploy --fail-level WARNING` → exit 0 (green).
- [ ] 4.2 `python manage.py test` for the touched area passes (new settings tests).
- [ ] 4.3 `python manage.py check` (existing ci.yml command) still passes.
- [ ] 4.4 Run the full repo suite / affected app tests to confirm REQ-4 (existing jobs not broken).

## Phase 5: Documentation

- [ ] 5.1 Add a brief comment in `security.yml` noting the job enforces Django deployment checks and why W008 is expected to be silenced.

## Phase 6: Commit

- [ ] 6.1 Commit `config/settings.py`, `.github/workflows/security.yml`, and the added test with a conventional message referencing `013-check-deploy-ci`.
