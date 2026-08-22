# Proposal

## Intent

Introduce a Redis-backed caching layer to cut repetitive database load and
response latency on the application's most expensive read paths: the Dashboard
KPI/aggregation queries and the public read-only DRF API endpoints. Cached data
MUST carry a bounded TTL and an explicit, key-scoped invalidation strategy so
that content stays fresh without manual cache flushes. The default cache today
is Django's in-process `LocMemCache` (per Python process), which is ineffective
the moment the app runs under multiple Gunicorn workers.

## Scope In / Out

### In
- Configure a `CACHES['default']` Redis backend in `config/settings.py`, driven
  by environment variables, with a local-memory fallback for development and CI.
- Add the `redis` (redis-py) client dependency to `requirements.txt`.
- Cache the expensive, user-agnostic Dashboard aggregations in
  `apps/dashboard/views/dashboard/dashboard.py` (the `Sum`/`Exists` commercial
  income queries and the forecast/alert series) keyed by `range`/`income_range`
  with a 5-minute TTL.
- Cache the read-only public API responses in `apps/api/views.py` (the
  `AllowAny` list endpoints) keyed by full request path + normalized query
  string.
- Provide graceful degradation: if Redis is disabled or unreachable, the app
  MUST keep serving (fall back to the in-process cache / uncached) and MUST NOT
  raise a 500.

### Out
- Invalidation-on-every-write cache busting for all models. We rely on TTL plus
  targeted, key-scoped invalidation for the chosen views only.
- Caching of authenticated, user-specific, or mutable endpoints beyond the
  listed public API.
- Caching the per-client block (`client_active_subs`, `client_invoices`, etc.)
  inside `DashboardView.get_context_data` — those are user-specific and MUST
  remain computed per request to avoid cross-user data leakage.
- Session or session-cache backend migration (sessions stay DB-backed).

## Approach

### Current state (grounding — read-only investigation)
- `config/settings.py` defines **no** `CACHES` setting. The project reads config
  directly via `os.getenv` (e.g. `DEBUG = os.getenv('DEBUG', 'False') == 'True'`
  at `config/settings.py:21`), so Django falls back to the default
  in-process `LocMemCache`. A grep for `CACHES` / `CACHE_BACKEND` reads in
  `config/settings.py` returns nothing.
- The only cache consumer today is `rate_limit_ip` in
  `apps/core/utils.py:56-75`, which does `from django.core.cache import cache`
  (line 62) and `cache.set(cache_key, count + 1, timeout=window)` (line 70)
  against that default cache. Under multiple Gunicorn workers this limiter is
  per-process and therefore ineffective cluster-wide — it silently benefits once
  the default cache becomes a shared Redis instance.
- `apps/core/management/commands/generate_env.py:219` emits
  `CACHE_BACKEND=django.core.cache.backends.locmem.LocMemCache` into `.env`, but
  `config/settings.py` never reads `CACHE_BACKEND`. It is currently an unused
  default.
- `requirements.txt:12` pins `Django==5.1.4` and the file contains **no**
  `redis` or `django-redis` entry. Because Django >= 4.0 ships a native Redis
  cache backend (`django.core.cache.backends.redis.RedisCache`), **no
  third-party `django-redis` package is required** for this change.

### Planned changes
1. **Dependency** — add a pinned `redis` entry to `requirements.txt`, matching
   the file's exact-pin style (e.g. `redis==5.2.1`). No `django-redis` needed.
2. **Settings** — in `config/settings.py`, add a `CACHES` dict using the same
   `os.getenv(..., 'False') == 'True'` convention already used at line 21:
   - `USE_REDIS_CACHE = os.getenv('USE_REDIS_CACHE', 'False') == 'True'`.
   - When `USE_REDIS_CACHE` is truthy:
     `'default': { 'BACKEND': 'django.core.cache.backends.redis.RedisCache',
     'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
     'OPTIONS': { 'CLIENT_CLASS': 'django.core.cache.backends.redis.RedisClient' } }`.
   - Otherwise keep `django.core.cache.backends.locmem.LocMemCache` so local dev
     and CI run without a Redis server.
3. **generate_env** — replace the dead `CACHE_BACKEND` emission at
   `apps/core/management/commands/generate_env.py:219` with
   `REDIS_URL=redis://127.0.0.1:6379/1` and `USE_REDIS_CACHE=False` for dev
   (`--production` emits `True`).
4. **Dashboard** — in `apps/dashboard/views/dashboard/dashboard.py`, wrap only
   the expensive shared aggregations (commercial `billed_qs`/`paid_qs` at lines
   222-235, the forecast series, and the alerts block) with
   `cache.get`/`cache.set` keyed by `dashboard:kpi:{range}:{income_range}` with
   TTL 300s. Leave the per-client `client_*` block (lines 105-129) computed
   per request.
5. **API** — add a reusable cache decorator/mixin and apply it to the `AllowAny`
   list endpoints in `apps/api/views.py` (`StationListAPIView`,
   `ForecastAPIView`, `WeatherReportListAPIView`,
   `ScientificPublicationListAPIView`, `ServiceListAPIView`,
   `EarlyWarningListAPIView`, `TropicalCycloneListAPIView`,
   `StormWarningListAPIView`, `StationObservationView`). Keys are built from the
   full request path + normalized query string; TTL ranges 60s (volatile:
   observations, warnings) to 300s (stable: stations, publications, services).

## Acceptance Criteria

- [ ] `requirements.txt` contains a pinned `redis` entry and `pip install -r requirements.txt` succeeds.
- [ ] `config/settings.py` defines `CACHES['default']` as `RedisCache` whose `LOCATION` is driven by the `REDIS_URL` env var.
- [ ] With `USE_REDIS_CACHE=False` (default), the app boots and the full relevant test suite passes with no Redis server running (LocMemCache fallback).
- [ ] With `USE_REDIS_CACHE=True` and Redis reachable, Dashboard shared KPIs/series are served from cache and recomputed at most once per `range`/`income_range` per 5-minute TTL.
- [ ] Public API list endpoints return cached responses keyed by request path + query params; a cache hit avoids re-executing the underlying queryset.
- [ ] Per-client Dashboard data (`client_*`) is NEVER served from a shared cache key (no cross-user leakage).
- [ ] If Redis is unreachable while `USE_REDIS_CACHE=True`, requests degrade to uncached/LocMemCache behavior and never raise a 500.
- [ ] `python manage.py check` passes and `python manage.py test apps.api apps.dashboard apps.core` is green.

## Rollback

- Remove the `CACHES` block from `config/settings.py` and drop `REDIS_URL` /
  `USE_REDIS_CACHE` from `.env` (regenerate via `python manage.py generate_env`).
  The app returns to the default `LocMemCache` behavior and no Redis server is
  required at runtime.
- Delete the `redis` line from `requirements.txt`. This is non-breaking: already
  installed environments keep the package; fresh installs simply omit it.
- No database migrations are introduced by this change, so rollback requires no
  migration reversal.
