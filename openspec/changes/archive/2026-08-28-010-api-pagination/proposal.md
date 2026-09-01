# Proposal: API Pagination for DRF List Endpoints

## Intent

The DRF `REST_FRAMEWORK` config in `config/settings.py:291` defines no
`DEFAULT_PAGINATION_CLASS` or `PAGE_SIZE`. Every list endpoint in
`apps/api/views.py` therefore returns the full queryset unpaginated — an
unbounded-scalability risk as observations, stations, warnings, and publications
grow. This change introduces standard DRF pagination while protecting the one
internal consumer (`map_station.js`) that expects a flat array.

## Scope

### In Scope
- Add global DRF pagination in `config/settings.py`.
- Exempt `StationListAPIView` from pagination to keep `map_station.js` working.
- Let remaining list endpoints inherit global pagination.
- Confirm drf-spectacular documents the new envelope automatically.

### Out of Scope
- Detail endpoints (`StationObservationView`, `ForecastAPIView`) — single objects.
- Frontend rewrite of `map_station.js` / `home-forecast.js`.
- Other live SDD changes (002–008).
- Model / migration / URL changes.

## Capabilities

### New Capabilities
- `api-pagination`: DRF list endpoints return a paginated envelope
  (`count`, `next`, `previous`, `results`) with `PAGE_SIZE=50`, except
  `StationListAPIView`, which stays unpaginated for `map_station.js` compatibility.

### Modified Capabilities
- None (no existing OpenSpec capability covers the API list endpoints; this
  introduces the capability).

## Approach

1. In `config/settings.py:291` add
   `DEFAULT_PAGINATION_CLASS = 'rest_framework.pagination.PageNumberPagination'`
   and `REST_FRAMEWORK['PAGE_SIZE'] = 50`.
   - **Why `PageNumberPagination`** over `LimitOffsetPagination`: simpler `?page=N`
     contract, drf-spectacular documents it out of the box, and the dataset size
     (tens to low thousands) does not need offset cursors. `LimitOffset` is the
     fallback if precise external slicing is later required.
2. In `apps/api/views.py` set `StationListAPIView.pagination_class = None` to
   protect `static/dist/js/map_station.js:62-68` (`data.forEach(station => ...)`,
   expects a flat array). Stations are only ~6 records, so unpaginated is safe.
3. All other `ListAPIView` subclasses
   (`EarlyWarningListAPIView`, `TropicalCycloneListAPIView`,
   `StormWarningListAPIView`, `WeatherReportListAPIView`,
   `ScientificPublicationListAPIView`, `ServiceListAPIView`) inherit global
   pagination with no code change. `ServiceListAPIView` stays paginated (small
   public dataset) but is documented.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `config/settings.py` | Modified | Add `DEFAULT_PAGINATION_CLASS` + `PAGE_SIZE` |
| `apps/api/views.py` | Modified | `StationListAPIView.pagination_class = None` |
| `apps/api/views.py` (other list views) | Behavior change | Inherit global pagination (no code edit) |
| `static/dist/js/map_station.js` | Unchanged | Protected by `StationListAPIView` exemption |
| `openspec/changes/010-api-pagination/specs/010-api-pagination/spec.md` | New | Delta spec (sdd-spec phase) |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| External clients expecting a flat array break | Med | Standard REST envelope; documented in `/api/doc/`; only public list endpoints change |
| `map_station.js` breaks | Low | Exempt `StationListAPIView` (`pagination_class=None`) |

## Rollback Plan

Revert `config/settings.py` and `apps/api/views.py` via `git checkout`; no
migrations. Run `collectstatic` if the static schema is cached. drf-spectacular
regenerates the OpenAPI schema on the next request.

## Dependencies

- drf-spectacular (already configured) auto-reflects pagination in OpenAPI.

## Success Criteria

- [ ] `REST_FRAMEWORK` sets `DEFAULT_PAGINATION_CLASS` + `PAGE_SIZE=50`.
- [ ] List endpoints (except stations) return `{count, next, previous, results}`.
- [ ] `/api/stations/` still returns a flat array; `map_station.js` unaffected.
- [ ] `/api/doc/` shows the paginated schema.
- [ ] `python manage.py test apps.api` passes.
