# Design — 003-cache-redis

## 1. Problem statement (anchored to current code)

The application has **no explicit cache configuration**. `config/settings.py`
defines no `CACHES` setting (grep for `CACHES`/`CACHE_BACKEND` reads returns
nothing), so Django uses its default in-process `LocMemCache` — one cache
instance per Python process.

Concrete pain points observed in the current code:

- **`apps/core/utils.py:56-75`** — `rate_limit_ip` uses
  `from django.core.cache import cache` (line 62) and `cache.set(...)` (line 70)
  against that default cache. With multiple Gunicorn workers this limiter is
  per-process and therefore ineffective cluster-wide.
- **`apps/dashboard/views/dashboard/dashboard.py:222-235`** — `get_context_data`
  runs `Sum`/`Exists` aggregation queries (`billed_qs`, `paid_qs`) plus forecast
  and alert series on every request, regardless of `range`/`income_range`.
- **`apps/api/views.py` + `apps/api/urls.py`** — the `AllowAny` list endpoints
  (`stations`, `forecast`, `weather-reports`, `publications`, `services`,
  `early-warnings`, `tropical-cyclones`, `storm-warnings`, `station-observation`)
  re-run the same querysets for identical requests.
- **`apps/core/management/commands/generate_env.py:219`** emits an unused
  `CACHE_BACKEND=...LocMemCache` default that `config/settings.py` never reads.
- **`requirements.txt:12`** pins `Django==5.1.4`; there is no `redis` or
  `django-redis` dependency.

## 2. Backend decision (tradeoff)

| Option | Pros | Cons |
|---|---|---|
| Native `django.core.cache.backends.redis.RedisCache` (Django >= 4.0) | No extra Django dependency, first-party support, connection pooling, `cache`/`cacheops`-style API | Requires `redis` (redis-py) package |
| Third-party `django-redis` | Familiar to some teams, extra features (compression, sentinel) | Unnecessary dependency for Django 5.1.4; slower release cadence |

**Decision:** use the native `RedisCache` backend. It requires only the `redis`
client package and removes the need for `django-redis`. This matches the intent
("django-redis / cache backend") while picking the canonical, lower-dependency
path.

## 3. Configuration design

Add to `config/settings.py`, mirroring the existing `os.getenv(...) == 'True'`
convention at `config/settings.py:21`:

```python
USE_REDIS_CACHE = os.getenv('USE_REDIS_CACHE', 'False') == 'True'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
}

if USE_REDIS_CACHE:
    CACHES['default'] = {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django.core.cache.backends.redis.RedisClient',
        },
    }
```

- `REDIS_URL` default `redis://127.0.0.1:6379/1` keeps local runs working.
- When `USE_REDIS_CACHE` is false/absent, the in-process `LocMemCache` is kept,
  so dev and CI need no Redis server.
- `apps/core/management/commands/generate_env.py:219` is updated to emit
  `REDIS_URL=redis://127.0.0.1:6379/1` and `USE_REDIS_CACHE=False` (dev) /
  `True` (production) instead of the dead `CACHE_BACKEND`.

## 4. Cache key design

### Dashboard (shared aggregates only)
- Key: `dashboard:kpi:{range}:{income_range}`
- TTL: 300s
- Scope: only the expensive user-agnostic aggregations
  (`billed_qs`/`paid_qs` lines 222-235, forecast series, alerts block).
- **MUST NOT** cache the per-client block (`client_active_subs`,
  `client_invoices`, etc., lines 105-129) — those are user-specific and caching
  them under a shared key would leak data across users. They stay per-request.

### Public API (read-only, `AllowAny`)
- Key: `api:{request.path}:{sorted_normalized_querystring}`
- TTL: 60s for volatile sources (observations, warnings, early/tropical/storm),
  300s for stable sources (stations, publications, services, forecast).
- All listed endpoints return identical data regardless of the caller, so a
  global shared key is safe.

## 5. Invalidation strategy

- **Primary:** time-based expiry (TTL) — simple, bounded staleness.
- **Secondary (optional, key-scoped):** explicit `cache.delete(pattern)` hooks
  on model `save`/`delete` signals for `Forecasts`, `Warning`, `WeatherReport`,
  `Service`, `Station`, `ScientificPublication` to drop the affected
  `api:*` keys. Out of scope for the first iteration; TTL alone satisfies the
  acceptance criteria.
- No full-flush / cache-clear admin action is introduced.

## 6. Resilience & degradation

- The native `RedisCache` raises connection errors only when actually touched.
  Wrap cache reads in a `try/except` that, on `redis.exceptions.RedisError`
  (or `django.core.cache.backends.redis.RedisCache` connection failure), treats
  the entry as a miss and computes live (and optionally skips writing). This
  guarantees no 500 when Redis is down while `USE_REDIS_CACHE=True`.
- `USE_REDIS_CACHE=False` (default) bypasses Redis entirely via LocMemCache.

## 7. Testing strategy

- `apps.core`: a test asserting `rate_limit_ip` still functions with the default
  cache (regression guard for the shared-cache side effect).
- `apps.dashboard`: a test that calls `DashboardView` twice within the TTL and
  asserts the aggregation queryset is executed once (e.g. via
  `django.db.connection.queries` or a query-count assertion), and a test that
  two different users each see their own `client_*` data (no leakage).
- `apps.api`: tests for cache hit/miss and key uniqueness per query params
  (different query strings -> different keys; identical -> cache hit).
- A settings-level test: with `USE_REDIS_CACHE=False`, `CACHES['default']`
  backend is `LocMemCache`; with `True` and a mock/real Redis, it is
  `RedisCache`.
- Run `python manage.py check` and
  `python manage.py test apps.api apps.dashboard apps.core` before marking done.

## 8. Files touched (plan, not yet applied)

| File | Change |
|---|---|
| `requirements.txt` | Add pinned `redis` entry |
| `config/settings.py` | Add `USE_REDIS_CACHE` flag + `CACHES` (RedisCache / LocMemCache fallback) |
| `apps/core/management/commands/generate_env.py:219` | Emit `REDIS_URL` + `USE_REDIS_CACHE` (replace dead `CACHE_BACKEND`) |
| `apps/dashboard/views/dashboard/dashboard.py` | Cache shared KPI/series aggregations (not the client block) |
| `apps/api/views.py` | Add cache decorator/mixin; apply to `AllowAny` list endpoints |
