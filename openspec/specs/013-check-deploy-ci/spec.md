# deploy-check-gate Specification

## Purpose

Enforce Django's deployment security system checks in CI so that a regression in the
production security posture fails the pipeline. The change (a) adds a `deploy-check` CI job
running `python manage.py check --deploy --fail-level WARNING` under the production profile,
(b) fixes `X_FRAME_OPTIONS` (W019) for real by setting it to `DENY`, and (c) intentionally
silences `security.W008` because Nginx terminates TLS and redirects to HTTPS. The job generates
its own `SECRET_KEY`/`ENCRYPTION_KEY` pair, so the `SECRET_KEY` deployment check is exercised
against a real encrypted key rather than being waved away by a random one.

## Requirements

### Requirement: CI Runs Deployment System Checks

The repository MUST run `python manage.py check --deploy --fail-level WARNING` in CI on every
pull request targeting `main` and on every push to `main`, so deployment security checks are
evaluated automatically. The command MUST run with `PRODUCTION` present in the environment, so
that `config/settings/production.py` is the profile under test.

#### Scenario: Job runs on pull request

- GIVEN a pull request is opened against `main`
- WHEN GitHub Actions evaluates the workflows
- THEN the `deploy-check` job SHALL execute `python manage.py check --deploy --fail-level WARNING`

#### Scenario: Job runs on push to main

- GIVEN a push is made to `main`
- WHEN GitHub Actions evaluates the workflows
- THEN the `deploy-check` job SHALL execute `python manage.py check --deploy --fail-level WARNING`

#### Scenario: The production profile is the one under test

- GIVEN the `deploy-check` job
- WHEN it invokes `python manage.py check --deploy --fail-level WARNING`
- THEN `PRODUCTION` SHALL be present in the step environment
- AND `config/settings/production.py` SHALL be the settings module being loaded

#### Scenario: The gate does not depend on the changed-app filter

- GIVEN a pull request that touches no app under `apps/`
- WHEN GitHub Actions evaluates the workflows
- THEN the `deploy-check` job SHALL run regardless of the `detect` job's `full` output

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

### Requirement: CI Generates Its Own Secret Key Material

The `deploy-check` job MUST NOT depend on any real secret. It MUST generate, at run time, a
`SECRET_KEY` encrypted with a freshly generated `ENCRYPTION_KEY`, using the same primitives as
the `generate_env` management command (`Fernet.generate_key()` for the encryption key and
`get_random_secret_key()` for the plaintext), and MUST NOT persist any of it to the repository.

#### Scenario: No real secret is required

- GIVEN CI runs without a `.env` file (`.env` is git-ignored) and without any repository secret
- WHEN the `deploy-check` job generates its key material
- THEN no pre-existing `SECRET_KEY` or `ENCRYPTION_KEY` SHALL be needed
- AND the generated values SHALL NOT be written to a tracked path

#### Scenario: The generated pair is a valid Fernet pair

- GIVEN the job generated `ENCRYPTION_KEY` with `Fernet.generate_key()`
- WHEN the job encrypts the plaintext secret with it
- THEN `config/settings/base.py` `decrypt_secret_key` SHALL recover the plaintext
- AND `config/settings/production.py` SHALL NOT raise for missing `SECRET_KEY`

#### Scenario: The plaintext secret does not trip security.W009

- GIVEN the job generated the plaintext secret
- WHEN that plaintext is produced
- THEN it SHALL be produced by `django.core.management.utils.get_random_secret_key`
- AND `security.W009` SHALL NOT fire, so the gate cannot fail for a non-security reason

### Requirement: Ephemeral SECRET_KEY Fallback Warns

`config/settings/base.py` MUST keep the `get_random_secret_key()` fallback when no
`SECRET_KEY`/`ENCRYPTION_KEY` pair can be decrypted, because failing closed there would make
the `generate_env` management command unrunnable: `manage.py` imports the settings before
dispatching the command, so the key generator would refuse to start. The fallback MUST
nonetheless emit a visible warning, so that reaching it can never again be silent. The warning
MUST be emitted through `warnings.warn` (not the `logging` module), because it is raised while
the settings module is being imported, i.e. before `LOGGING` is configured.

#### Scenario: A missing key warns in a non-production profile

- GIVEN no `.env` and no `SECRET_KEY`/`ENCRYPTION_KEY` in the environment
- WHEN a non-production profile (dev or testing) is loaded
- THEN `SECRET_KEY` SHALL fall back to a randomly generated key
- AND an `EphemeralSecretKeyWarning` SHALL be emitted naming `generate_env` as the fix

#### Scenario: The key generator can still boot

- GIVEN a checkout with no `.env`
- WHEN `python manage.py generate_env` is invoked
- THEN the settings import SHALL NOT raise
- AND the command SHALL run and write a valid encrypted pair

#### Scenario: Production still fails closed

- GIVEN no `.env` and no `SECRET_KEY`/`ENCRYPTION_KEY` in the environment
- WHEN the production profile is loaded
- THEN `config/settings/production.py` SHALL raise `ImproperlyConfigured`
- AND it SHALL NOT fall back to an ephemeral key

#### Scenario: A valid pair does not warn

- GIVEN a `.env` whose `SECRET_KEY` decrypts with its `ENCRYPTION_KEY`
- WHEN any profile is loaded
- THEN no ephemeral-key warning SHALL be emitted

### Requirement: Production Security Posture Hardened

`config/settings/base.py` MUST set `X_FRAME_OPTIONS = 'DENY'` (resolving W019) and MUST include
`security.W008` in `SILENCED_SYSTEM_CHECKS` with a comment explaining that Nginx terminates
TLS and performs the HTTPS redirect. `config/settings/production.py` MUST pin `DEBUG = False`
rather than inherit it from `base.py`, so that a `DEBUG=True` in a production `.env` cannot serve
tracebacks containing server paths. After these changes, `check --deploy --fail-level WARNING`
MUST pass under the production profile with a generated key.

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

- GIVEN `X_FRAME_OPTIONS = 'DENY'`, `security.W008` is silenced, and the job generated a valid
  Fernet key pair
- WHEN `python manage.py check --deploy --fail-level WARNING` runs with `PRODUCTION` in the
  environment
- THEN the command SHALL exit zero
- AND no deployment WARNING/ERROR SHALL remain

### Requirement: Production Rejects The Console Email Backend

`config/settings/production.py` MUST raise `ImproperlyConfigured` when the resolved
`EMAIL_BACKEND` is `django.core.mail.backends.console.EmailBackend`, because a console backend
in production discards every message without raising an error. The check MUST compare the
backend path and MUST NOT reject any other backend, including the real
`config.custom_email_backend.CustomSTARTTLSBackend`. The raise message MUST name
`python manage.py generate_env --production` as the fix.

#### Scenario: Console backend in production is rejected

- GIVEN the production profile is loaded with `EMAIL_BACKEND` set to
  `django.core.mail.backends.console.EmailBackend`
- WHEN the settings module is imported
- THEN it SHALL raise `ImproperlyConfigured`
- AND the message SHALL mention `python manage.py generate_env --production`

#### Scenario: A real SMTP backend is accepted

- GIVEN the production profile is loaded with `EMAIL_BACKEND` set to
  `config.custom_email_backend.CustomSTARTTLSBackend` or
  `django.core.mail.backends.smtp.EmailBackend`
- WHEN the settings module is imported
- THEN it SHALL NOT raise
- AND `check --deploy` SHALL pass

#### Scenario: Dev defaults to console only when the environment is silent

- GIVEN a development checkout whose `.env` does not define `EMAIL_BACKEND`
- WHEN the dev profile is loaded
- THEN `EMAIL_BACKEND` SHALL be `django.core.mail.backends.console.EmailBackend`
- AND GIVEN a `.env` that does define `EMAIL_BACKEND`
- THEN the explicit value SHALL win, so real email sending stays testable from dev

### Requirement: Existing CI Jobs Are Not Broken

Adding the `deploy-check` job MUST NOT modify or break the existing CI jobs (Django tests,
Ruff lint, Bandit, djlint templates, pre-commit, migrations check) in `.github/workflows/`.

#### Scenario: Existing jobs remain intact

- GIVEN the `deploy-check` job is added to CI
- WHEN the full CI suite runs on a pull request
- THEN the existing jobs (tests, lint, bandit, templates, pre-commit, migrations) SHALL run unchanged
- AND their behavior SHALL NOT regress due to this change

#### Scenario: The gate needs no real secret to be meaningful

- GIVEN CI runs without a `.env` and without any repository secret
- WHEN `check --deploy` loads settings under the production profile
- THEN the `SECRET_KEY` deployment check SHALL be satisfied by the job's generated key
- AND no SECRET_KEY-related deployment warning SHALL fail the job
