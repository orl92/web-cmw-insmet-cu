# Tasks — 003-cache-redis

## Phase 1 — Dependency & Configuration
- [ ] Add a pinned `redis` entry to `requirements.txt` (matching exact-pin style)
- [ ] Add `USE_REDIS_CACHE = os.getenv('USE_REDIS_CACHE', 'False') == 'True'` and a `CACHES` block to `config/settings.py` (RedisCache default + LocMemCache fallback)
- [ ] Drive `CACHES['default'].LOCATION` from the `REDIS_URL` env var (default `redis://127.0.0.1:6379/1`)
- [ ] Update `apps/core/management/commands/generate_env.py:219` to emit `REDIS_URL` + `USE_REDIS_CACHE` (replace the unused `CACHE_BACKEND` default)

## Phase 2 — Dashboard caching
- [ ] Wrap the shared KPI/series aggregations in `apps/dashboard/views/dashboard/dashboard.py::get_context_data` (lines 222-235 and the forecast/alerts blocks) with `cache.get`/`cache.set` keyed by `dashboard:kpi:{range}:{income_range}`, TTL 300s
- [ ] Ensure only user-agnostic data is cached; keep the `client_*` block (lines 105-129) computed per request (no cross-user leakage)
- [ ] Verify cached values are picklable/serializable for the Redis backend

## Phase 3 — API caching
- [ ] Implement a reusable cache decorator/mixin for read-only API views in `apps/api/views.py`
- [ ] Apply it to the `AllowAny` list endpoints (`StationListAPIView`, `ForecastAPIView`, `WeatherReportListAPIView`, `ScientificPublicationListAPIView`, `ServiceListAPIView`, `EarlyWarningListAPIView`, `TropicalCycloneListAPIView`, `StormWarningListAPIView`, `StationObservationView`)
- [ ] Key by full request path + normalized/sorted query string; TTL 60s (volatile) to 300s (stable) per endpoint
- [ ] Add tests asserting cache hit/miss and key uniqueness per query params

## Phase 4 — Resilience & Verification
- [ ] Wrap cache reads so a Redis outage degrades to uncached/LocMemCache behavior (no 500) when `USE_REDIS_CACHE=True`
- [ ] `python manage.py check` passes
- [ ] `python manage.py test apps.api apps.dashboard apps.core` is green
- [ ] Confirm `rate_limit_ip` (`apps/core/utils.py:56-75`) still works against the (now shared) default cache
