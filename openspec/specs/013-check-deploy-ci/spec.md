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

The `deploy-check` job MUST NOT depend on any real secret. It MUST generate, at run
time, a `SECRET_KEY` encrypted with a freshly generated `ENCRYPTION_KEY`, by invoking the
same generator the production server uses (`scripts/generate_env.py`), and MUST NOT persist
any of it to a tracked path. The generated `.env` MUST be written outside the checkout (the
runner's temp directory), because the job does not run production and produces a
SQLite/DEBUG file that must not be mistaken for a deployable one.

The job MUST call the generator with `--development` and propagate only `SECRET_KEY` and
`ENCRYPTION_KEY` into the step environment, deleting the file afterwards. The profile under
test comes from `PRODUCTION` in the environment, not from the shape of the generated file,
so the gate needs the key pair and nothing else.

#### Scenario: No real secret is required

- GIVEN CI runs without a `.env` file (`.env` is git-ignored) and without any repository secret
- WHEN the `deploy-check` job generates its key material
- THEN no pre-existing `SECRET_KEY` or `ENCRYPTION_KEY` SHALL be needed
- AND the generated values SHALL NOT be written to a tracked path

#### Scenario: The gate uses the production generator

- GIVEN a regression in `scripts/generate_env.py` that makes it emit an undecryptable pair
- WHEN the `deploy-check` job runs the generator
- THEN `config/settings/base.py` `decrypt_secret_key` SHALL fail to recover the plaintext
- AND `check --deploy` SHALL NOT pass on a key the server could not actually use

#### Scenario: The gate needs only the key pair

- GIVEN the job generated a development-shaped `.env` outside the checkout
- WHEN it prepares the step environment
- THEN it SHALL propagate only `SECRET_KEY` and `ENCRYPTION_KEY`
- AND it SHALL delete the generated file
- AND `PRODUCTION` in the environment, not the file's shape, SHALL select the profile

#### Scenario: The generated pair is a valid Fernet pair

- GIVEN the job ran the generator with `ENCRYPTION_KEY` from `Fernet.generate_key()`
- WHEN it encrypts the plaintext secret with it
- THEN `config/settings/base.py` `decrypt_secret_key` SHALL recover the plaintext
- AND `config/settings/production.py` SHALL NOT raise for missing `SECRET_KEY`

#### Scenario: The plaintext secret does not trip security.W009

- GIVEN the job generated the plaintext secret
- WHEN that plaintext is produced
- THEN it SHALL be produced by `django.core.management.utils.get_random_secret_key`
- AND `security.W009` SHALL NOT fire, so the gate cannot fail for a non-security reason

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
`python scripts/generate_env.py --production` as the fix.

#### Scenario: Console backend in production is rejected

- GIVEN the production profile is loaded with `EMAIL_BACKEND` set to
  `django.core.mail.backends.console.EmailBackend`
- WHEN the settings module is imported
- THEN it SHALL raise `ImproperlyConfigured`
- AND the message SHALL mention `python scripts/generate_env.py --production`

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

### Requirement: Key Material Generation Lives Outside Django

The key generator MUST be a standalone script that does not import Django, settings, or
`manage.py`. It MUST NOT be a management command, and it MUST NOT be reintroduced as one.

#### Scenario: A management command would be unbootable

- GIVEN a management command that generates key material
- WHEN Django dispatches it
- THEN `manage.py` SHALL have already imported the settings via `django.setup()`
- AND a fail-closed `load_secret_key()` SHALL have raised `ImproperlyConfigured` before
  the command body ran
- AND the command would be unreachable in exactly the state that needs it

#### Scenario: The generator is runnable in a clean checkout

- GIVEN a checkout with no `.env` and no `ENCRYPTION_KEY` in the environment
- WHEN `python scripts/generate_env.py --production` is invoked
- THEN it SHALL write a valid encrypted pair
- AND the application SHALL boot afterwards without any further key material

### Requirement: Settings Fail Closed Without Decryptable Key Material

`config/settings/base.py` `load_secret_key()` MUST raise `ImproperlyConfigured` in every
profile when there is no `SECRET_KEY`, no `ENCRYPTION_KEY`, or when the pair does not
decrypt. It MUST NOT fall back to a generated key and MUST NOT warn and continue. The
`testing` profile is the single exception: it injects a deterministic pair before
importing `base`, so CI and a clean-checkout `manage.py test` boot without secrets.

#### Scenario: A checkout with no .env refuses to start

- GIVEN no `.env` and neither `SECRET_KEY` nor `ENCRYPTION_KEY` in the environment
- WHEN any profile is loaded
- THEN `load_secret_key()` SHALL raise `ImproperlyConfigured`
- AND the message SHALL name `python scripts/generate_env.py` as the fix

#### Scenario: Half-configured key material is refused

- GIVEN a `SECRET_KEY` with no `ENCRYPTION_KEY`, or an `ENCRYPTION_KEY` with no `SECRET_KEY`
- WHEN the settings are loaded
- THEN `load_secret_key()` SHALL raise `ImproperlyConfigured`
- AND the message SHALL distinguish which half is missing

#### Scenario: A mismatched pair is refused

- GIVEN a `.env` whose `SECRET_KEY` does not decrypt with the available `ENCRYPTION_KEY`
- WHEN the settings are loaded
- THEN `load_secret_key()` SHALL raise `ImproperlyConfigured`
- AND it SHALL NOT substitute a generated key

#### Scenario: The testing profile still boots without secrets

- GIVEN no `.env` and no key material in the environment
- WHEN the `testing` profile is selected
- THEN it SHALL inject a deterministic pair before importing `base`
- AND `load_secret_key()` SHALL NOT raise
- AND the pair SHALL NOT be written to any file

### Requirement: The Decryption Key Is Not Stored Beside The Ciphertext

In production, the file holding the encrypted `SECRET_KEY` (`.env` inside the application
directory) MUST NOT also hold the `ENCRYPTION_KEY` that decrypts it. The generator MUST
write the decryption key to a separate file outside the application directory
(`/etc/webcmp/encryption.env`), and the systemd units MUST load it with `EnvironmentFile=-`
so the service still starts, and fails with the actionable `load_secret_key()` error, when
that file is absent.

#### Scenario: A leaked .env does not hand over the key

- GIVEN production `.env` containing a `SECRET_KEY` encrypted with a key held only in
  `/etc/webcmp/encryption.env`
- WHEN the `.env` file alone is disclosed
- THEN the ciphertext SHALL NOT be decryptable from the disclosed material

#### Scenario: The decryption key is not web-reachable

- GIVEN the application directory is served by the application and the `/etc/webcmp`
  path is not under it
- WHEN the static or media routes are served
- THEN `/etc/webcmp/encryption.env` SHALL NOT be reachable

#### Scenario: A missing decryption key file still surfaces the real error

- GIVEN `/etc/webcmp/encryption.env` does not exist
- WHEN the `webcmp` service starts
- THEN systemd SHALL NOT abort with its own `EnvironmentFile` error
- AND `load_secret_key()` SHALL raise `ImproperlyConfigured` naming the missing file
