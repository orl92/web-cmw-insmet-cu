# Tasks — 003-cache-redis

## Phase 1 — Dependency & Configuration
- [x] Add a pinned `redis` entry to `requirements.txt` (matching exact-pin style)
- [x] Add `USE_REDIS_CACHE = os.getenv('USE_REDIS_CACHE', 'False') == 'True'` and a `CACHES` block to `config/settings.py` (RedisCache default + LocMemCache fallback)
- [x] Drive `CACHES['default'].LOCATION` from the `REDIS_URL` env var (default `redis://127.0.0.1:6379/1`)
- [x] Update `apps/core/management/commands/generate_env.py:219` to emit `REDIS_URL` + `USE_REDIS_CACHE` (replace the unused `CACHE_BACKEND` default)

## Phase 2 — Dashboard caching
- [x] Wrap the shared KPI/series aggregations in `apps/dashboard/views/dashboard/dashboard.py::get_context_data` (lines 222-235 and the forecast/alerts blocks) with `cache.get`/`cache.set` keyed by `dashboard:kpi:{range}:{income_range}`, TTL 300s
- [x] Ensure only user-agnostic data is cached; keep the `client_*` block (lines 105-129) computed per request (no cross-user leakage)
- [x] Verify cached values are picklable/serializable for the Redis backend

## Phase 3 — API caching
- [x] Implement a reusable cache decorator/mixin for read-only API views in `apps/api/views.py`
- [x] Apply it to the `AllowAny` list endpoints (`StationListAPIView`, `ForecastAPIView`, `WeatherReportListAPIView`, `ScientificPublicationListAPIView`, `ServiceListAPIView`, `EarlyWarningListAPIView`, `TropicalCycloneListAPIView`, `StormWarningListAPIView`, `StationObservationView`)
- [x] Key by full request path + normalized/sorted query string; TTL 60s (volatile) to 300s (stable) per endpoint
- [x] Add tests asserting cache hit/miss and key uniqueness per query params

## Phase 4 — Resilience & Verification
- [x] Wrap cache reads so a Redis outage degrades to uncached/LocMemCache behavior (no 500) when `USE_REDIS_CACHE=True`
- [x] `python manage.py check` passes
- [x] `python manage.py test apps.api apps.dashboard apps.core` is green
- [x] Confirm `rate_limit_ip` (`apps/core/utils.py:56-75`) still works against the (now shared) default cache
