# deploy-check-gate Specification

## Purpose

Enforce Django's deployment security system checks in CI so that a regression in the
production security posture fails the pipeline. The change (a) adds a `deploy-check` CI job
running `python manage.py check --deploy --fail-level WARNING`, (b) fixes `X_FRAME_OPTIONS`
(W019) for real by setting it to `DENY`, and (c) intentionally silences `security.W008`
because Nginx terminates TLS and redirects to HTTPS. The `SECRET_KEY` deployment check is
verified not to fire in CI (`IS_PRODUCTION=False` leads to a random key).

## Requirements

### Requirement: CI Runs Deployment System Checks

The repository MUST run `python manage.py check --deploy --fail-level WARNING` in CI on every
pull request targeting `main` and on every push to `main`, so deployment security checks are
evaluated automatically.

#### Scenario: Job runs on pull request

- GIVEN a pull request is opened against `main`
- WHEN GitHub Actions evaluates the workflows
- THEN the `deploy-check` job SHALL execute `python manage.py check --deploy --fail-level WARNING`

#### Scenario: Job runs on push to main

- GIVEN a push is made to `main`
- WHEN GitHub Actions evaluates the workflows
- THEN the `deploy-check` job SHALL execute `python manage.py check --deploy --fail-level WARNING`

### Requirement: Job Fails On Any Warning Or Error

The `deploy-check` job MUST fail the pipeline when `check --deploy` reports any WARNING or
ERROR (i.e. a non-zero exit code), preventing deployment-security regressions from merging.

#### Scenario: A deployment warning fails the pipeline

- GIVEN a settings change reintroduces a deployment WARNING (e.g. W019)
- WHEN the `deploy-check` job runs `check --deploy --fail-level WARNING`
- THEN the job SHALL exit non-zero
- AND the CI pipeline SHALL be marked failed

#### Scenario: A clean deployment posture passes

- GIVEN no deployment WARNING/ERROR is present
- WHEN the `deploy-check` job runs `check --deploy --fail-level WARNING`
- THEN the job SHALL exit zero
- AND the CI pipeline SHALL be marked passed

### Requirement: Production Security Posture Hardened

`config/settings.py` MUST set `X_FRAME_OPTIONS = 'DENY'` (resolving W019) and MUST include
`security.W008` in `SILENCED_SYSTEM_CHECKS` with a comment explaining that Nginx terminates
TLS and performs the HTTPS redirect. After these changes, `check --deploy --fail-level WARNING`
MUST pass on a fresh checkout (no `.env`, `DEBUG` defaults to `False`).

#### Scenario: X_FRAME_OPTIONS is DENY

- GIVEN the Django settings are loaded
- WHEN `settings.X_FRAME_OPTIONS` is inspected
- THEN it SHALL equal `'DENY'`

#### Scenario: W008 is intentionally silenced

- GIVEN the Django settings are loaded
- WHEN `settings.SILENCED_SYSTEM_CHECKS` is inspected
- THEN it SHALL contain `'security.W008'`
- AND a code comment SHALL document that Nginx terminates TLS and redirects to HTTPS

#### Scenario: check --deploy is green after hardening

- GIVEN `X_FRAME_OPTIONS = 'DENY'` and `security.W008` is silenced
- WHEN `python manage.py check --deploy --fail-level WARNING` runs on a fresh checkout with no `.env`
- THEN the command SHALL exit zero
- AND no deployment WARNING/ERROR SHALL remain

### Requirement: Existing CI Jobs Are Not Broken

Adding the `deploy-check` job MUST NOT modify or break the existing CI jobs (Django tests,
Ruff lint, Bandit, djlint templates, pre-commit, migrations check) in `.github/workflows/`.

#### Scenario: Existing jobs remain intact

- GIVEN the `deploy-check` job is added to CI
- WHEN the full CI suite runs on a pull request
- THEN the existing jobs (tests, lint, bandit, templates, pre-commit, migrations) SHALL run unchanged
- AND their behavior SHALL NOT regress due to this change

#### Scenario: SECRET_KEY check does not false-positive in CI

- GIVEN CI runs without a `.env` and without the `PRODUCTION` env var (`IS_PRODUCTION=False`)
- WHEN `check --deploy` loads settings
- THEN `SECRET_KEY` SHALL fall back to a randomly generated key
- AND no SECRET_KEY-related deployment warning SHALL fail the job
