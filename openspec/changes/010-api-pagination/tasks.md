# Tasks: API Pagination for DRF List Endpoints

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~120 (settings + views + tests) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

## Phase 1: Implementation

- [x] 1.1 In `config/settings.py` (REST_FRAMEWORK dict, line ~291) add `DEFAULT_PAGINATION_CLASS = 'rest_framework.pagination.PageNumberPagination'` and `PAGE_SIZE = 50`.
- [x] 1.2 In `apps/api/views.py` set `StationListAPIView.pagination_class = None` (line ~106) to keep `/api/stations/` a flat array for `map_station.js:62-68`.
- [x] 1.3 Confirm `EarlyWarning/TropicalCyclone/StormWarning/WeatherReport/ScientificPublication/Service` list views inherit global pagination with no code edit (covered by envelope tests).

## Phase 2: Tests (strict_tdd, apps/api/tests/)

- [x] 2.1 Settings test: assert `settings.REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS']` equals `'rest_framework.pagination.PageNumberPagination'` and `PAGE_SIZE == 50`.
- [x] 2.2 Integration: `GET /api/stations/` returns a flat list (no `results`, `count`, `next`, `previous`).
- [x] 2.3 Integration: `GET /api/early-warnings/` returns `{count, next, previous, results}` with `len(results) <= 50`; `?page=2` reachable (`previous` not null, different slice).
- [x] 2.4 Integration: `GET /api/forecast/<date>/` returns a single object (no `results` key).
- [x] 2.5 OpenAPI: `GET /api/schema/` exposes `count/results` for affected list endpoints and documents stations as a plain array.

## Phase 3: Verification

- [x] 3.1 Run `python manage.py test apps.api` — all new tests pass.
- [x] 3.2 Run `python manage.py check` — no system check errors.

## Phase 4: Documentation

- [x] 4.1 Confirm `/api/doc/` and `/api/redoc/` reflect the paginated envelope (drf-spectacular auto); note if a schema regeneration/collectstatic is required.

## Phase 5: Commit

- [x] 5.1 Commit `config/settings.py`, `apps/api/views.py`, and the added tests with a conventional message referencing `010-api-pagination`. **(Orchestrator performs the commit; apply sub-agent does not commit.)**
