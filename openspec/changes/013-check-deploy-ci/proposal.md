# Proposal: Add `manage.py check --deploy` Gate to CI

## Intent

CI today runs `python manage.py check` (without `--deploy`) in `.github/workflows/ci.yml`
and Bandit SAST in `.github/workflows/security.yml`, but **no job enforces Django's
deployment security system checks** (`security.W0xx`). A production-misconfigured security
header can therefore ship to production undetected. This change adds a CI job that runs
`python manage.py check --deploy --fail-level WARNING` and fails the pipeline on any
WARNING/ERROR, after we (a) **genuinely fix** `X_FRAME_OPTIONS` (W019) and (b)
**intentionally silence** `SECURE_SSL_REDIRECT` (W008) because Nginx terminates TLS and
performs the HTTPS redirect — Django must not also redirect.

## Scope

### In Scope
- Add a `deploy-check` job to `.github/workflows/security.yml` (runs on PR + push to main).
- Fix `X_FRAME_OPTIONS = 'DENY'` in `config/settings.py` (resolves W019 for real).
- Silence `security.W008` via `SILENCED_SYSTEM_CHECKS` in `config/settings.py` with an
  explanatory comment (Nginx terminates TLS; the redirect is Nginx's responsibility).

### Out of Scope
- Bandit (`security.yml` already has it) — not modified by this change.
- SECRET_KEY hardening: verified NOT triggered in CI (see Design / empirical finding).
- Model / migration / URL / template changes.
- Forcing `SECURE_SSL_REDIRECT = True`: explicitly out of scope — it is an intentional
  Nginx responsibility, not a Django one.

## Capabilities

### New Capabilities
- `deploy-check-gate`: CI fails the pipeline when Django's deployment system checks report
  any WARNING or ERROR, preventing regressions in the production security posture.

### Modified Capabilities
- None (no prior OpenSpec capability covers the production system-check gate).

## Approach

1. In `config/settings.py:288` change `X_FRAME_OPTIONS = 'SAMEORIGIN'` to
   `X_FRAME_OPTIONS = 'DENY'`. This resolves W019 by hardening clickjacking protection for
   real rather than hiding the warning.
   - **Verification step**: confirm no first-party view is embedded in a cross-origin (or
     even same-origin) `<iframe>` that would break under `DENY`. The app is a standard
     Tabler Django app with no documented framing use; if a legitimate framing need is found,
     revisit rather than reverting silently.
2. In `config/settings.py` add `SILENCED_SYSTEM_CHECKS = ['security.W008']` with a comment
   stating Nginx terminates TLS and issues the HTTPS redirect, so Django intentionally does
   not set `SECURE_SSL_REDIRECT = True`. This silences W008 without weakening security.
3. In `.github/workflows/security.yml` add a `deploy-check` job that installs
   `requirements-dev.txt` and runs `python manage.py check --deploy --fail-level WARNING`.
   The job runs on a **fresh checkout with no `.env`** — `DEBUG` defaults to `False`, so the
   production security block is active, and system checks open **no database connection**, so
   no DB is required. This is exactly the condition already verified in CI.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `config/settings.py` | Modified | `X_FRAME_OPTIONS = 'DENY'` (line 288); add `SILENCED_SYSTEM_CHECKS = ['security.W008']`. |
| `.github/workflows/security.yml` | Modified | Add `deploy-check` job running `check --deploy --fail-level WARNING`. |
| `apps/core/management/commands/generate_env.py` | Unchanged | Not invoked by the new job (fresh checkout is sufficient). |
| Existing `ci.yml` / `security.yml` (bandit) jobs | Unchanged | New job is additive; existing jobs unaffected. |
| `openspec/changes/013-check-deploy-ci/specs/013-check-deploy-ci/spec.md` | New | Delta spec (sdd-spec phase). |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `DENY` breaks a first-party iframe embed | Low | Verify no framing use in app; if needed, scope `X_FRAME_OPTIONS` per-view instead of reverting. |
| New job is flaky / needs DB in CI | Low | `check --deploy` is settings-only; it does not open a DB connection; runs on fresh checkout. |
| `SILENCED_SYSTEM_CHECKS` accidentally hides a future real W008 regression | Low | Comment documents the reason; the gate still fails on every other WARNING/ERROR. |
| Other deployment WARNINGs surface after the gate is on | Med | Run the job during verify phase; any new WARNING is addressed (or explicitly silenced with comment) before merge. |

## Rollback Plan

- Revert `config/settings.py` and `.github/workflows/security.yml` via `git checkout`; no
  migrations. The `deploy-check` job is additive and independent of Bandit/test/lint jobs.
- `SILENCED_SYSTEM_CHECKS` revert restores W008 visibility locally.

## Dependencies

- Django system-check framework (`manage.py check --deploy`) — already available.
- `requirements-dev.txt` — already installed by the existing `security.yml` Bandit job.

## Success Criteria

- [ ] REQ-1: CI runs `manage.py check --deploy` on PR and push to main.
- [ ] REQ-2: the `deploy-check` job fails the pipeline on any WARNING/ERROR finding.
- [ ] REQ-3: `config/settings.py` sets `X_FRAME_OPTIONS = 'DENY'` and silences
  `security.W008` (documented); `check --deploy --fail-level WARNING` passes green.
- [ ] REQ-4: existing CI jobs (tests, lint, bandit, templates, pre-commit, migrations) are
  unchanged and still pass.

(End of file)
