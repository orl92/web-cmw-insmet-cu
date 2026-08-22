# Tasks — 009-debug-toolbar

## Phase 1 — Dependency

- [x] **1.1** Add `django-debug-toolbar==4.4.2` to `requirements-dev.txt` (dev-only; confirm it is absent from runtime `requirements.txt`).

## Phase 2 — Settings guard

- [x] **2.1** In `config/settings.py`, insert a guarded block immediately after `DEBUG` (line 21): under `if DEBUG and not IS_PRODUCTION:` append `debug_toolbar` to `INSTALLED_APPS`, append `debug_toolbar.middleware.DebugToolbarMiddleware` to `MIDDLEWARE`, and set `INTERNAL_IPS = ['127.0.0.1', '::1']`.

## Phase 3 — URL mount

- [x] **3.1** In `config/urls.py`, tighten the existing `if settings.DEBUG:` gate (line 42) to `if settings.DEBUG and not settings.IS_PRODUCTION:` and append `path('__debug__/', include('debug_toolbar.urls'))` to `urlpatterns`.

## Phase 4 — Tests

- [x] **4.1** Add a test that verifies the toolbar does NOT load in production mode (`IS_PRODUCTION` set, or `DEBUG=False`) and DOES load in dev mode (`DEBUG=True and not IS_PRODUCTION`) by inspecting `INSTALLED_APPS`/`MIDDLEWARE`.

## Phase 5 — Verification

- [x] **5.1** Run `python manage.py check` and confirm it passes; run `python manage.py test` and confirm the suite is unaffected.
