# Spec — 009-debug-toolbar

## Delta Requirements

### DBG-1: Development-only activation

The `django-debug-toolbar` application and middleware MUST be loaded only when `DEBUG` is `True` and `IS_PRODUCTION` is `False`.

- **Given** the environment has `DEBUG=True` and `IS_PRODUCTION=False`
- **When** Django settings are loaded
- **Then** `debug_toolbar` MUST be present in `INSTALLED_APPS` and `debug_toolbar.middleware.DebugToolbarMiddleware` MUST be present in `MIDDLEWARE`

- **Given** the environment has `IS_PRODUCTION=True` (regardless of `DEBUG`)
- **When** Django settings are loaded
- **Then** `debug_toolbar` MUST NOT be present in `INSTALLED_APPS` and `DebugToolbarMiddleware` MUST NOT be present in `MIDDLEWARE`

- **Given** the environment has `DEBUG=False` (regardless of `IS_PRODUCTION`)
- **When** Django settings are loaded
- **Then** `debug_toolbar` MUST NOT be present in `INSTALLED_APPS`

### DBG-2: Internal IP allowlist

When the toolbar is active, `INTERNAL_IPS` SHOULD include `'127.0.0.1'` and `'::1'` so the toolbar renders for localhost requests.

- **Given** the toolbar is active (`DEBUG=True and not IS_PRODUCTION`)
- **When** settings are loaded
- **Then** `INTERNAL_IPS` MUST contain `'127.0.0.1'` and `'::1'`

### DBG-3: URL mounting

The toolbar URLs MUST be mounted at `/__debug__/` only under the dev guard.

- **Given** `DEBUG=True` and `IS_PRODUCTION=False`
- **When** `config/urls.py` URL patterns are resolved
- **Then** a route for `path('__debug__/', include('debug_toolbar.urls'))` MUST be present

- **Given** `IS_PRODUCTION=True` or `DEBUG=False`
- **When** `config/urls.py` URL patterns are resolved
- **Then** no `/__debug__/` route MUST be registered

### DBG-4: Zero production impact

The runtime dependency footprint MUST remain unchanged in production.

- **Given** the project's runtime `requirements.txt`
- **When** the change is applied
- **Then** `django-debug-toolbar` MUST NOT appear in `requirements.txt` (it MAY appear only in `requirements-dev.txt`)

- **Given** the applied change
- **When** a production deployment is built
- **Then** no migrations, model changes, or business URL changes MUST be introduced

### DBG-5: Check and test suite integrity

- **Given** the change is implemented
- **When** `python manage.py check` is executed
- **Then** it MUST pass without errors in both dev and production configuration

- **Given** the change is implemented
- **When** `python manage.py test` is executed
- **Then** the existing test suite MUST be unaffected (no new failures, no new runtime dependency required to run it)
