# Design: Add `manage.py check --deploy` Gate to CI

## Technical Approach

Add a `deploy-check` job to `.github/workflows/security.yml` that installs
`requirements-dev.txt` and runs `python manage.py check --deploy --fail-level WARNING`. The
job runs on a **fresh checkout with no `.env`**. Because `DEBUG` defaults to `False`
(`config/settings.py:21` — `os.getenv('DEBUG', 'False') == 'True'`), the production security
block at `config/settings.py:49` (`if not DEBUG:`) is active, so `SECURE_HSTS_SECONDS`,
`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, etc. are set and their warnings (W004/W012/W016)
do **not** fire. Django system checks are settings-only and open **no database connection**,
so no DB is required and no `.env`/secrets are needed.

Before the gate can be green, two settings changes are required:

1. `X_FRAME_OPTIONS` is changed from `'SAMEORIGIN'` to `'DENY'` (fixes W019 genuinely).
2. `SILENCED_SYSTEM_CHECKS = ['security.W008']` is added, documenting that Nginx terminates
   TLS and performs the HTTPS redirect, so Django intentionally leaves `SECURE_SSL_REDIRECT`
   as `False`.

## Architecture Decisions

| Decision | Options | Tradeoff | Chosen |
|----------|---------|----------|--------|
| CI production simulation | Fresh checkout (no `.env`, `DEBUG` defaults `False`) vs `generate_env --production` + `PRODUCTION=true` | Fresh checkout is the exact condition already verified in CI, needs no secrets, and never opens a DB. `generate_env --production` exercises the `IS_PRODUCTION=True` branch but writes placeholder DB/email creds and is heavier. Both surface only W008+W019. | Fresh checkout (no `.env`); `generate_env --production` noted as optional stricter check |
| W008 handling | Silence via `SILENCED_SYSTEM_CHECKS` vs set `SECURE_SSL_REDIRECT=True` | Nginx already terminates TLS and redirects to HTTPS; making Django also redirect would double-redirect / break the proxy contract. Silencing with a comment preserves the correct architecture. | Silence W008 with explanatory comment |
| W019 handling | `X_FRAME_OPTIONS='DENY'` vs keep `SAMEORIGIN` | `DENY` is the safe default for an app with no documented framing; the warning exists to push toward it. | `'DENY'` |
| Job location | New job in `security.yml` vs new job in `ci.yml` | `security.yml` already groups security tooling (Bandit) and is the natural home; keeps `ci.yml` unaffected. | `deploy-check` in `security.yml` |

## CI Simulation Mechanism (empirically verified)

The verified CI behavior (no `.env`):

```
$ python manage.py check --deploy --fail-level WARNING
WARNINGS:
?: (security.W008) SECURE_SSL_REDIRECT is not set to True ...
?: (security.W019) X_FRAME_OPTIONS is not set to 'DENY' ...
System check identified 2 issues (0 silenced).   # exit 1
```

- **Why only W008 + W019** (and not W004/W012/W016/W018/W020): with no `.env`, `DEBUG`
  defaults to `False`, so the `if not DEBUG:` security block runs and sets
  `SECURE_HSTS_SECONDS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_CONTENT_TYPE_NOSNIFF`,
  `SECURE_PROXY_SSL_HEADER`, etc. `ALLOWED_HOSTS` defaults to `localhost,127.0.0.1` (no W020),
  and `IS_PRODUCTION=False` → `SECRET_KEY` falls back to `get_random_secret_key()` (no
  SECRET_KEY warning). Hence the **only** surfaced deployment warnings are W008 and W019.
- **Local run discrepancy (for context)**: a local checkout *with* a `.env` containing
  `DEBUG=True` skips the security block, which surfaces W004/W012/W016/W018 as well. That is
  a local-env artifact, not the CI condition. The CI job must therefore NOT rely on a `.env`
  and must keep `DEBUG=False` (the default).
- **SECRET_KEY risk does NOT materialize**: `config/settings.py:37-46` —
  `if SECRET_KEY is None and IS_PRODUCTION: raise ... else: SECRET_KEY = get_random_secret_key()`.
  In CI `IS_PRODUCTION=False` (no `PRODUCTION` env var), so a random key is used and
  `check --deploy` does not fail on `SECRET_KEY`. No CI secret is required.

## Data Flow

```
GitHub Actions (PR / push to main)
   │  actions/checkout@v4  (fresh checkout, NO .env written)
   ▼
setup-python 3.12 + cache pip
   ▼
pip install -r requirements-dev.txt
   ▼
python manage.py check --deploy --fail-level WARNING
   │  settings load: DEBUG=False (default) → security block active
   │  system checks: settings-only, NO DB connection
   ▼
exit 0  (green)  after W019 fixed + W008 silenced
exit 1  (red)    on any WARNING/ERROR
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `config/settings.py` | Modify | `X_FRAME_OPTIONS = 'DENY'` (line 288). Add `SILENCED_SYSTEM_CHECKS = ['security.W008']` with a comment explaining Nginx terminates TLS. |
| `.github/workflows/security.yml` | Modify | Add `deploy-check` job: `pip install -r requirements-dev.txt` then `python manage.py check --deploy --fail-level WARNING`. Triggers: PR + push to `main` (mirrors the Bandit job). |
| `apps/core/management/commands/generate_env.py` | Unchanged | Not used by the gate (fresh checkout is sufficient). |
| `config/test_runner.py`, `ci.yml` | Unchanged | Out of scope. |

## Interfaces / Contracts

The gate consumes the Django CLI contract:

```
python manage.py check --deploy --fail-level WARNING
  --deploy            : enable deployment system checks (security.W0xx)
  --fail-level WARNING: any WARNING or ERROR returns a non-zero exit code
```

No application interface, URL, model, or API contract changes. The only observable behavior
change is the hardened `X-Frame-Options` response header (`DENY` instead of `SAMEORIGIN`).

## Testing Strategy

Repo uses `strict_tdd`; tests live next to apps. The gate is primarily a CI contract, but the
settings invariants SHOULD be covered by a unit test so a local `manage.py test` catches a
regression:

| Layer | What to Test | Approach |
|-------|--------------|----------|
| Settings unit | `X_FRAME_OPTIONS == 'DENY'` | Assert `django.conf.settings.X_FRAME_OPTIONS == 'DENY'` (new test in `apps/core/tests/` or a `config` test module). |
| Settings unit | `security.W008` is silenced | Assert `'security.W008' in settings.SILENCED_SYSTEM_CHECKS`. |
| CI contract | `check --deploy` is green after fixes | Run `python manage.py check --deploy --fail-level WARNING` locally on a fresh checkout; document the expected output (0 issues). This is also what the new job enforces. |
| Regression | Existing `ci.yml` jobs unaffected | Confirm `python manage.py check`, `test`, `ruff`, `djlint`, `pre-commit`, `makemigrations --check` still pass. |

## Threat Matrix

`X_FRAME_OPTIONS='DENY'` **tightens** the clickjacking boundary (W019). `SILENCED_SYSTEM_CHECKS`
for W008 is a **documented, intentional** suppression of a check whose remediation belongs to
Nginx, not Django — it does not weaken runtime security. The CI YAML change adds a read-only
(settings-only) gate; it executes no untrusted input, no subprocess beyond `manage.py`, and
introduces no secret handling. Risk class: configuration hardening + CI enforcement only.

## Migration / Rollout

No migrations, no model/URL/template changes. Enable by merging the two-file diff
(`config/settings.py` + `security.yml`). The gate takes effect on the next PR/push to `main`.

## Rollback

`git checkout -- config/settings.py .github/workflows/security.yml` (no migrations). The
`deploy-check` job is additive and independent of Bandit/test/lint jobs; reverting it removes
only the gate. Reverting the settings restores `X_FRAME_OPTIONS='SAMEORIGIN'` and W008 visibility.

## Open Questions

- None blocking. If a legitimate first-party framing need is discovered during the verify
  phase, scope `X_FRAME_OPTIONS` per-view (middleware/per-response) instead of reverting to
  `SAMEORIGIN`.
