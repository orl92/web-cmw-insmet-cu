# Design: API Pagination for DRF List Endpoints

## Technical Approach

Enable DRF's global `PageNumberPagination` by setting `DEFAULT_PAGINATION_CLASS`
and `PAGE_SIZE=50` inside the existing `REST_FRAMEWORK` dict in
`config/settings.py:291`. Every `ListAPIView` in `apps/api/views.py` then inherits
the paginated envelope (`count`, `next`, `previous`, `results`) with zero code
edits. `StationListAPIView` is explicitly opted out (`pagination_class = None`) to
keep `static/dist/js/map_station.js:62-68` working on a flat array. Detail views
(`StationObservationView`, `ForecastAPIView`) are `GenericAPIView` returning a single
object; DRF never paginates a non-list response, so they are unaffected by design.

## Architecture Decisions

| Decision | Options | Tradeoff | Chosen |
|----------|---------|----------|--------|
| Pagination style | `PageNumberPagination` vs `LimitOffsetPagination` | `?page=N` is simpler; drf-spectacular documents it automatically; dataset is tens–low thousands (no offset-cursor need). `LimitOffset` is the fallback if precise external slicing is later required. | `PageNumberPagination` |
| Stations exemption | `pagination_class=None` vs refactor `map_station.js` | `map_station.js` is committed dist JS doing `data.forEach`; ~6 stations, safe unpaginated. Refactoring dist JS is out of scope and riskier. | `pagination_class=None` |
| Scope of change | Global default vs per-view | Global default covers all current + future `ListAPIView`s; only stations need an override. Least code, consistent contract. | Global default |

## Data Flow

```
Client GET /api/early-warnings/
        │
        ▼
EarlyWarningListAPIView (ListAPIView)
        │  get_queryset() → filtered MeteoWarning
        ▼
DRF paginator (DEFAULT_PAGINATION_CLASS, PAGE_SIZE=50)
        │  wraps: {count, next, previous, results:[≤50]}
        ▼
Response JSON envelope

Client GET /api/stations/
        │
        ▼
StationListAPIView  (pagination_class = None)
        ▼
Flat JSON array  →  map_station.js data.forEach(...)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `config/settings.py` | Modify | Add `DEFAULT_PAGINATION_CLASS = 'rest_framework.pagination.PageNumberPagination'` and `PAGE_SIZE = 50` to `REST_FRAMEWORK` (line 291). |
| `apps/api/views.py` | Modify | Add `pagination_class = None` to `StationListAPIView` (line ~106). |
| `apps/api/views.py` (other list views) | Behavior change only | `EarlyWarningListAPIView`, `TropicalCycloneListAPIView`, `StormWarningListAPIView`, `WeatherReportListAPIView`, `ScientificPublicationListAPIView`, `ServiceListAPIView` inherit global pagination — no edit. |
| `static/dist/js/map_station.js` | Unchanged | Protected by stations exemption. |
| `static/dist/js/home-forecast.js` | Unchanged | Forecast detail is a single object. |

## Interfaces / Contracts

Paginated envelope (DRF standard):

```json
{
  "count": 120,
  "next": "https://host/api/early-warnings/?page=2",
  "previous": null,
  "results": [ { "...": "serialized item" } ]
}
```

Stations endpoint stays a bare array `[ { "...": "station" } ]`. Detail endpoints
return a single object `{ "...": "forecast" }`.

## Testing Strategy

Repo uses `strict_tdd`; tests live in `apps/api/tests/`. Use Django
`APITestCase` + `APIClient` and seed data via factories/model creates.

| Layer | What to Test | Approach |
|-------|--------------|----------|
| Settings | `REST_FRAMEWORK` has `DEFAULT_PAGINATION_CLASS` and `PAGE_SIZE == 50` | Assert against `django.conf.settings.REST_FRAMEWORK`. |
| Unit/API | `/api/stations/` returns a flat array (no `results`) | GET; assert `isinstance(resp.data, list)` and `'results' not in resp.data`. |
| Unit/API | `/api/early-warnings/` returns envelope, `len(results) <= 50`; `?page=2` reachable | Seed >50 `MeteoWarning`; GET page 1 asserts `count`/`next`/`previous`/`results`; GET `?page=2` asserts `previous` is not null and a different slice. |
| Unit/API | `/api/forecast/<date>/` returns a single object (no `results`) | GET valid date; assert `'results' not in resp.data` and it is a dict. |
| Contract | drf-spectacular reflects envelope | `GET /api/schema/`; assert affected list endpoints expose `count`/`results`, stations documented as array. |

## Threat Matrix

`N/A — no routing, shell, subprocess, VCS/PR automation, executable-file
classification, or process-integration boundary is changed.` This is a DRF
configuration + one view attribute; no untrusted-input execution path is added.

## Migration / Rollout

No migrations, no model/URL changes. After deploy, drf-spectacular regenerates the
OpenAPI schema on the next `/api/schema/` request; `collectstatic` is only needed if
a cached schema asset is served. Enable by merging the two-file diff.

## Rollback

`git checkout -- config/settings.py apps/api/views.py` (no migrations). drf-spectacular
rebuilds the schema automatically. If a CDN/proxy caches `/api/doc/`, purge it.

## Open Questions

None.
