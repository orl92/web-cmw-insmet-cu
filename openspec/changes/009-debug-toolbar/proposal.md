# Proposal: Add django-debug-toolbar as a Development-Only Tool

## Intent

Developer productivity in this Django 5.1.4 project currently has no in-browser profiling. Diagnosing N+1 queries, template render cost, cache hits, and request/signal flow requires manual `connection.queries` or external tools. Adding `django-debug-toolbar` gives immediate SQL/cache/template/signals panels — but it must remain **completely inert in production** to preserve the project's fail-closed DEBUG/DB posture.

## Scope

### In Scope
- Add `django-debug-toolbar` to `requirements-dev.txt` (dev-only dependency; never in runtime `requirements.txt`).
- Guard-load it in `config/settings.py` only when `DEBUG and not IS_PRODUCTION`.
- Set `INTERNAL_IPS` and append `DebugToolbarMiddleware` under the same guard.
- Mount toolbar URLs at `/__debug__/` in `config/urls.py` under the same guard.

### Out of Scope
- Any production behavior change, new features, or UI work.
- Changes to runtime `requirements.txt`, migrations, or persisted data.
- AGENTS.md documentation (optional follow-up, not required).

## Approach

**Current reality (read-only evidence):**
- `config/settings.py:19` `IS_PRODUCTION = 'PRODUCTION' in os.environ`; `:21` `DEBUG = os.getenv('DEBUG','False')=='True'`.
- No `INTERNAL_IPS` is defined today (grep returned clean).
- Dev/prod branching already follows a fail-closed `if IS_PRODUCTION:` / `elif` pattern (WhiteNoise middleware at `:344-348`), establishing the convention to mirror.
- `config/urls.py:42` already gates `static()` on `settings.DEBUG` — reuse that hook with a stricter guard.

**Concrete plan:**
1. `requirements-dev.txt`: append `django-debug-toolbar==4.4.2` (latest 4.x compatible with Django 5.1.4; confirm pin at implementation).
2. `config/settings.py`, right after the `IS_PRODUCTION`/`DEBUG` definitions (`:21`), add a guarded block:
   ```python
   if DEBUG and not IS_PRODUCTION:
       INSTALLED_APPS += ['debug_toolbar']
       MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
       INTERNAL_IPS = ['127.0.0.1', '::1']
   ```
   Appending to `MIDDLEWARE` is safe: `SessionMiddleware`/`AuthenticationMiddleware` populate `request.session`/`request.user` during the request phase, and `DebugToolbarMiddleware`'s response handling runs last, wrapping the final output. `INTERNAL_IPS` is required for the toolbar to render for localhost.
3. `config/urls.py`: tighten the existing `if settings.DEBUG:` block (`:42`) and mount the toolbar:
   ```python
   if settings.DEBUG and not settings.IS_PRODUCTION:
       urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
       urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
   ```

This keeps the toolbar fully inert in production: the dependency is absent from runtime `requirements.txt`, and even if `DEBUG` were ever `True` in prod, `IS_PRODUCTION` suppresses it.

## Acceptance Criteria

- [ ] `django-debug-toolbar` pinned in `requirements-dev.txt`, absent from `requirements.txt`.
- [ ] Toolbar loads only when `DEBUG and not IS_PRODUCTION`; verified by inspecting `INSTALLED_APPS`/`MIDDLEWARE` under each mode.
- [ ] Accessible at `/__debug__/` in local dev (with `INTERNAL_IPS` covering `127.0.0.1`).
- [ ] Zero production impact: no new runtime dependency, no migrations, no settings changes outside the guard.
- [ ] `python manage.py check` passes and the `python manage.py test` suite is unaffected.

## Rollback

Remove the guarded block from `config/settings.py` and `config/urls.py`, and drop `django-debug-toolbar` from `requirements-dev.txt`. No migrations or data changes are involved, so rollback is a pure source revert with zero persistence impact.
