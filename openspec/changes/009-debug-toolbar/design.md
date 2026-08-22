# Design — 009-debug-toolbar

## Objective

Add `django-debug-toolbar` as a **development-only** profiling tool that is **completely inert in production**. The project already enforces a fail-closed DEBUG/prod posture; this change mirrors that convention so the toolbar can never load outside a local dev environment.

## Current Reality (read-only evidence)

- `config/settings.py:19` — `IS_PRODUCTION = 'PRODUCTION' in os.environ`.
- `config/settings.py:21` — `DEBUG = os.getenv('DEBUG', 'False') == 'True'`.
- `config/settings.py:109` — `MIDDLEWARE = [...]` (list; safe to append).
- `config/settings.py:87` — `INSTALLED_APPS = [...]` (list; safe to append).
- No `INTERNAL_IPS` is defined today (grep returned clean) — the toolbar requires it to render for localhost.
- Dev/prod branching already uses a fail-closed `if IS_PRODUCTION:` / `elif` pattern (WhiteNoise at `config/settings.py:344-348`) — the guard below mirrors that convention.
- `config/urls.py:42` already gates `static()` on `settings.DEBUG` — reused and tightened with a stricter guard.
- `requirements-dev.txt` exists (ruff, bandit, pip-audit, djlint, pre-commit, setuptools, wheel) and contains no `django-debug-toolbar`.

## Dependencies

- Add `django-debug-toolbar==4.4.2` to `requirements-dev.txt` ONLY.
- MUST NOT appear in runtime `requirements.txt` (currently pinned `Django==5.1.4`).
- Version pin is fixed to the latest 4.x compatible with Django 5.1.4.

## Guarded block — `config/settings.py`

Insert immediately after the `DEBUG` definition (`config/settings.py:21`), under the same fail-closed logic used by WhiteNoise:

```python
if DEBUG and not IS_PRODUCTION:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1', '::1']
```

Rationale:
- Appending to `MIDDLEWARE` is safe. `SessionMiddleware`/`AuthenticationMiddleware` populate `request.session`/`request.user` during the request phase; `DebugToolbarMiddleware` wraps the response last and only acts when the client IP is in `INTERNAL_IPS`.
- `INTERNAL_IPS` is required for the toolbar to render for localhost requests.
- Because the block is gated on `not IS_PRODUCTION`, even a stray `DEBUG=True` in a production environment cannot enable the toolbar.

## URL mounting — `config/urls.py`

Tighten the existing gate (`config/urls.py:42`) and mount the toolbar URLs:

```python
if settings.DEBUG and not settings.IS_PRODUCTION:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
```

The toolbar is then reachable at `/__debug__/` in local dev.

## Out of Scope (explicit)

- No changes to runtime `requirements.txt` (no new production dependency).
- No model changes, no migrations (already absent from `.gitignore` tracking strategy — none generated).
- No changes to business URLs or views.
- No `AGENTS.md` documentation update (tracked as optional follow-up, not required).
- No production behavior change, new feature, or UI work.

## Verification

- `python manage.py check` passes in both dev and prod settings.
- A test asserts `debug_toolbar` is absent from `INSTALLED_APPS`/`MIDDLEWARE` when `IS_PRODUCTION` is set, and present when `DEBUG and not IS_PRODUCTION`.
- Existing test suite (`python manage.py test`) is unaffected.

## Rollback

Remove the guarded block from `config/settings.py` and `config/urls.py`, and drop `django-debug-toolbar` from `requirements-dev.txt`. No migrations or data changes are involved; rollback is a pure source revert with zero persistence impact.
