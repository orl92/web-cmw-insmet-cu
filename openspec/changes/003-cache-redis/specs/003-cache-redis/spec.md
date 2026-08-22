# Spec — cache-redis (delta requirements)

Capability: `cache-redis`
Status: proposed
Depends on: Django >= 4.0 native Redis cache backend

## Requirement CACHE-1: Redis backend MUST be environment-driven
The cache backend selection MUST be controlled by environment variables, with a
local-memory fallback when Redis is disabled.

- **SHALL** read `USE_REDIS_CACHE` from the environment via
  `os.getenv('USE_REDIS_CACHE', 'False') == 'True'` (mirroring
  `config/settings.py:21`).
- **SHALL** set `CACHES['default']` backend to
  `django.core.cache.backends.redis.RedisCache` when `USE_REDIS_CACHE` is true.
- **SHALL** set `LOCATION` from `REDIS_URL`
  (`redis://127.0.0.1:6379/1` default).
- **SHALL** default to `django.core.cache.backends.locmem.LocMemCache` when
  `USE_REDIS_CACHE` is false or unset.

### Scenario: Redis disabled (default)
- **Given** `USE_REDIS_CACHE` is unset or `"False"`
- **When** the application boots
- **Then** `CACHES['default']` backend is `LocMemCache` and no Redis connection is required

### Scenario: Redis enabled
- **Given** `USE_REDIS_CACHE="True"` and `REDIS_URL="redis://redis:6379/1"`
- **When** the application boots
- **Then** `CACHES['default']` backend is `RedisCache` with `LOCATION` equal to `redis://redis:6379/1`

## Requirement CACHE-2: Graceful degradation
The system MUST NOT fail with HTTP 500 when Redis is unreachable.

- **SHALL** treat a cache read/write failure under `USE_REDIS_CACHE=True` as a
  cache miss and compute data live.
- **SHALL** avoid writing through when the backend is unreachable.

### Scenario: Redis down while enabled
- **Given** `USE_REDIS_CACHE="True"` and the Redis server is unreachable
- **When** any cached view is requested
- **Then** the view returns a correct, uncached response and the request does not raise a 500

## Requirement CACHE-3: Dashboard shared aggregates MUST be cached
The expensive, user-agnostic Dashboard aggregations MUST be cached with a
bounded TTL.

- **SHALL** cache the commercial income queries (`billed_qs`/`paid_qs`,
  `apps/dashboard/views/dashboard/dashboard.py:222-235`), forecast series, and
  alerts block.
- **SHALL** key by `dashboard:kpi:{range}:{income_range}`.
- **SHALL** use a TTL of 300 seconds.
- **SHALL NOT** cache the per-client `client_*` block
  (`apps/dashboard/views/dashboard/dashboard.py:105-129`).

### Scenario: Repeated load within TTL
- **Given** a Dashboard request for `range=30d` and `income_range=12m`
- **When** the same Dashboard request is made again within 300s
- **Then** the aggregation querysets are NOT re-executed (served from cache)

### Scenario: No cross-user leakage
- **Given** user A and user B (both `Clientes`) request the Dashboard
- **When** their per-client sections are rendered
- **Then** each user sees only their own `client_*` data (never served from the shared cache key)

## Requirement CACHE-4: Public API read endpoints SHOULD be cached
The read-only `AllowAny` API endpoints SHOULD be cached to reduce DB load.

- **SHOULD** cache `StationListAPIView`, `ForecastAPIView`,
  `WeatherReportListAPIView`, `ScientificPublicationListAPIView`,
  `ServiceListAPIView`, `EarlyWarningListAPIView`, `TropicalCycloneListAPIView`,
  `StormWarningListAPIView`, and `StationObservationView`.
- **SHALL** key by request path + normalized/sorted query string.
- **SHALL** use TTL 60s for volatile sources (observations, warnings) and 300s
  for stable sources (stations, publications, services, forecast).

### Scenario: Identical requests hit cache
- **Given** two identical GET requests to a public list endpoint
- **When** the second request arrives within the TTL
- **Then** the underlying queryset is not re-executed (cache hit)

### Scenario: Distinct query params produce distinct keys
- **Given** GET `/api/stations/?province=1` and `/api/stations/?province=2`
- **When** both are requested
- **Then** they resolve to different cache keys and each computes its own result

## Requirement CACHE-5: Dependency footprint
- **SHALL** add the `redis` (redis-py) client to `requirements.txt`.
- **SHALL NOT** require the third-party `django-redis` package, because
  `Django==5.1.4` already ships a native Redis cache backend.

### Scenario: Fresh install
- **Given** a clean environment
- **When** `pip install -r requirements.txt` runs
- **Then** the `redis` package is installed and no `django-redis` package is required for the cache to function
