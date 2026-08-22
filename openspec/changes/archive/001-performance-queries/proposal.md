# Proposal: Optimize ORM query performance for `meteo` API and views

## Intent

Eliminate N+1 query patterns in the `apps/api` DRF list endpoints and the
`apps/meteo` HTML list views, by applying `select_related` / `prefetch_related`
wherever serializers or templates walk foreign-key / many-to-many relations, and
adding query-count instrumentation (`assertNumQueries`) so the optimizations
cannot regress. The `WarningListView` (a DataTables view) keeps its client-side
pagination; only its `user` relation is pre-joined.

## Scope In

- `apps/api/views.py` + `apps/api/serializers.py` — DRF `ListAPIView`
  endpoints: `StationListAPIView`, `EarlyWarningListAPIView`,
  `TropicalCycloneListAPIView`, `StormWarningListAPIView`,
  `WeatherReportListAPIView`, `ScientificPublicationListAPIView`.
- `apps/meteo/views/warning.py` — `WarningListView` (N+1 on `user`; renders a
  DataTables grid with client-side pagination, so the `context['objects']`
  full-queryset override is intentional, not a defect).
- New regression tests under `apps/api/tests/` and `apps/meteo/tests/`
  asserting bounded query counts.

## Scope Out

- `apps/commercial`, `apps/dashboard`, `apps/home` — outside the preserved
  intent. (`commercial` already uses `select_related` / `prefetch_related`
  throughout its views, per `apps/commercial/views/*`.)
- New DB indexes (`db_index`) — `Forecasts.date` is **already** indexed
  (`apps/meteo/models.py:63`). `Warning.warning_type`
  (`apps/meteo/models.py:288`), `Warning.valid_until` (`apps/meteo/models.py:296`)
  and `WeatherReport.report_type` (`apps/meteo/models.py:246`) are filtered but
  not indexed; index additions are explicitly out of the preserved intent and
  are deferred.
- `StationListView` (`apps/meteo/views/station.py`), `WeatherReportListView`
  (`apps/meteo/views/weather_report.py`) and `ForecastsListView`
  (`apps/meteo/views/forecast.py`) — already use `select_related` /
  `prefetch_related`. Their `context['objects'] = <full queryset>` is intentional
  because their templates extend `templates/layouts/list.html`, which renders a
  DataTables grid with client-side pagination (`templates/layouts/list.html:27,46-54`),
  exactly matching the project convention "vistas con DataTables cargan todos los
  registros". No change required.

## Approach

### A. API N+1 elimination (`apps/api/views.py`)

- `StationListAPIView.queryset` (line 104) is `Station.objects.all()`, but
  `StationSerializer` reads `province.code` / `province.name`
  (`apps/api/serializers.py:18-19`) → one extra query per station (N+1).
  **Fix:** `Station.objects.select_related('province')`.
- `EarlyWarningListAPIView` (lines 147-148), `TropicalCycloneListAPIView`
  (lines 155-156) and `StormWarningListAPIView` (lines 165-166) return
  `MeteoWarning.objects.filter(...)` with no `select_related`, while
  `WarningSerializer` reads `user.username` (`apps/api/serializers.py:105`) →
  N+1 per warning. **Fix:** append `.select_related('user')` to each queryset.
- `WeatherReportListAPIView.get_queryset` (lines 173-177) lacks
  `select_related`, while `WeatherReportSerializer` reads `user.username`
  (`apps/api/serializers.py:113`) → N+1 per report. **Fix:** `.select_related('user')`.
- `ScientificPublicationListAPIView.queryset` (line 181) is
  `ScientificPublication.objects.all()`, while `ScientificPublicationSerializer`
  reads `author.__str__` (FK) and `coauthors` (M2M, `StringRelatedField`)
  (`apps/api/serializers.py:121-122`) → N+1 on `author` plus N+1 on `coauthors`.
  **Fix:** `.select_related('author').prefetch_related('coauthors')`.
- `ForecastAPIView.queryset` (line 125) already
  `prefetch_related('regions', 'extended_days')`; the serializer re-filters the
  prefetched cache in Python (`apps/api/serializers.py:50,85`) — no N+1 is
  produced. **No change required.** Optional cleanup (design §Optional) uses an
  explicit `Prefetch(to_attr=...)` to avoid re-filtering the cache three times.
- `ServiceListAPIView` (lines 186-189) — `ServiceSerializer` exposes only scalar
  fields; no relation access. **No change required.**

### B. meteo HTML view (`apps/meteo/views/warning.py`)

- `WarningListView.get_queryset` (lines 90-91) returns
  `Warning.objects.filter(warning_type=...)` with no `select_related`. The template
  `layouts/list.html` (a DataTables grid) reads `object.user.get_full_name`
  (`warning/early_warning/list.html:26`) → N+1 on `User` only (it does NOT read
  `profile`). **Fix:** `.select_related('user')`.
- `WarningListView` sets `paginate_by = 20` (line 74) and `get_context_data`
  overrides `context['objects'] = self.get_queryset()` (line 103) with the full
  queryset. This is **correct and intended**: the view renders a DataTables grid
  that loads all records and paginates client-side (project convention: "vistas
  con DataTables cargan todos los registros"), so there is no server-side
  pagination to restore. `avisos.html` is a separate card layout used only by the
  public home warning pages, not by this view. No change to `get_context_data`.

### C. Query instrumentation (`assertNumQueries`)

- Extend `apps/api/tests/test_api.py` (already hosts `StationListAPITests`,
  `ForecastAPITests`) with `assertNumQueries` cases for every endpoint above.
- Add a `TestCase` in `apps/meteo/tests/` (e.g. `test_warning_views.py` or a new
  `test_performance.py`) asserting a bounded query count for `WarningListView`
  before/after the `select_related` + pagination fix.
- Tests are executed with the full app label: `python manage.py test apps.api apps.meteo`
  (Django 5.1.4 does not resolve short labels — see `requirements.txt`).

## Acceptance Criteria

- [ ] `StationListAPIView` returns station + province data with a single joined
      query (no per-station province lookup).
- [ ] `EarlyWarningListAPIView`, `TropicalCycloneListAPIView` and
      `StormWarningListAPIView` each resolve `user` in one joined query.
- [ ] `WeatherReportListAPIView` resolves `user` in one joined query.
- [ ] `ScientificPublicationListAPIView` resolves `author` and `coauthors` in at
      most two queries (author join + coauthors prefetch).
- [ ] `WarningListView` resolves `user` in a single joined query (proven by a new
      `assertNumQueries` test).
- [ ] `WarningListView` preserves its DataTables client-side pagination: the
      `context['objects']` full-queryset override is intentional and the view loads
      all records for client-side paging.
- [ ] New `assertNumQueries` tests pass for all affected endpoints / views under
      `apps.api` and `apps.meteo`.
- [ ] `python manage.py check` and
      `python manage.py test apps.api apps.meteo` both pass.

## Rollback

All changes are confined to `apps/api/views.py`, `apps/meteo/views/warning.py`
and new test files. No model or migration changes are introduced. Roll back via
`git revert` of the implementing commit; there is nothing to un-apply at the
database layer.
