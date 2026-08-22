# Spec — performance-queries

Delta requirements for change `001-performance-queries`. All scenarios are
expressed as Given/When/Then and use RFC2119 keywords (MUST, SHOULD, MAY).

## Requirement: API list endpoints MUST pre-join accessed relations

The DRF `ListAPIView` endpoints in `apps/api/views.py` SHALL issue a constant
(O(1)) number of queries regardless of the number of rows returned, by using
`select_related` / `prefetch_related` for every relation the serializer reads.

### Scenario: Station list resolves province without N+1
- **Given** the `StationListAPIView` queryset at `apps/api/views.py:104`
- **When** a client requests the station list and `StationSerializer` reads
  `province.code` / `province.name` (`apps/api/serializers.py:18-19`)
- **Then** the response MUST be produced with exactly one SQL query (station
  joined to province via `select_related('province')`)

### Scenario: Warning list endpoints resolve author without N+1
- **Given** `EarlyWarningListAPIView`, `TropicalCycloneListAPIView` and
  `StormWarningListAPIView` (`apps/api/views.py:143-166`)
- **When** a client requests any of them and `WarningSerializer` reads
  `user.username` (`apps/api/serializers.py:105`)
- **Then** the `user` relation MUST be resolved with `select_related('user')`
  in a single joined query

### Scenario: Weather report list resolves author without N+1
- **Given** `WeatherReportListAPIView` at `apps/api/views.py:169-177`
- **When** the serializer reads `user.username` (`apps/api/serializers.py:113`)
- **Then** the queryset MUST use `select_related('user')`

### Scenario: Scientific publication list resolves author and coauthors without N+1
- **Given** `ScientificPublicationListAPIView` at `apps/api/views.py:180-183`
- **When** `ScientificPublicationSerializer` reads `author.__str__` (FK) and
  `coauthors` (M2M, `StringRelatedField`) (`apps/api/serializers.py:121-122`)
- **Then** the queryset MUST use `select_related('author').prefetch_related('coauthors')`
  and resolve both relations in at most two queries

### Scenario: Already-optimized endpoints are unchanged
- **Given** `ForecastAPIView` (`apps/api/views.py:125`, already
  `prefetch_related('regions','extended_days')`) and `ServiceListAPIView`
  (`apps/api/views.py:186-189`, scalar-only serializer)
- **When** the change is applied
- **Then** these two endpoints MUST NOT require modification

## Requirement: `WarningListView` MUST pre-join relations and paginate server-side

The `WarningListView` in `apps/meteo/views/warning.py` SHALL pre-join the
relations its template walks and SHALL apply the configured `paginate_by`
server-side.

### Scenario: Warning HTML list resolves user and profile without N+1
- **Given** `WarningListView.get_queryset` at `apps/meteo/views/warning.py:90-91`
- **When** the template `templates/layouts/avisos.html:48,50` reads
  `warning.user.profile.get_avatar` and `warning.user.get_full_name`
- **Then** the queryset MUST use `select_related('user', 'user__profile')`
  (`Profile.user` is `OneToOneField(User, related_name='profile')`,
  `apps/user_auth/models.py:20`)

### Scenario: Warning HTML list applies server-side pagination
- **Given** `WarningListView` sets `paginate_by = 20`
  (`apps/meteo/views/warning.py:74`) and `templates/layouts/avisos.html` is a
  **non-DataTables** card layout that iterates `objects`
- **When** the list is rendered
- **Then** the view MUST NOT replace the context with the full queryset
  (`apps/meteo/views/warning.py:103` MUST be removed/adjusted) and the template
  MUST iterate the paginated `page_obj` and render the pagination control
  (`templates/includes/pagination.html` consumes `page_obj`)

## Requirement: Query counts MUST be guarded by regression tests

The project SHALL add `assertNumQueries` tests so the optimizations cannot
regress.

### Scenario: API endpoints are covered by query-count tests
- **Given** `apps/api/tests/test_api.py` (hosts `StationListAPITests`,
  `ForecastAPITests`)
- **When** the change is applied
- **Then** `assertNumQueries` cases MUST exist asserting the bounded counts:
  station=1, each warning endpoint=1, weather-report=1, publication=2,
  forecast=3

### Scenario: Warning HTML list is covered by a query-count test
- **Given** `apps/meteo/tests/`
- **When** the change is applied
- **Then** a `TestCase` MUST assert `WarningListView` uses a bounded query count
  (COUNT + one paginated page, with `user`/`user__profile` joined)

### Scenario: Tests use the full app label
- **Given** Django 5.2 in this project (per `AGENTS.md`)
- **When** the suite is executed
- **Then** it MUST be invoked as `python manage.py test apps.api apps.meteo`
  (short labels are not resolved)

## Non-Goals (explicitly out of scope)
- DB index additions (`db_index`) — `Forecasts.date` is already indexed
  (`apps/meteo/models.py:63`); `Warning.warning_type` / `valid_until` and
  `WeatherReport.report_type` may be indexed later but are NOT part of this change.
- `apps/commercial`, `apps/dashboard`, `apps/home` — outside the preserved intent.
- `StationListView`, `WeatherReportListView`, `ForecastsListView` — already
  correct and use DataTables client-side pagination (`templates/layouts/list.html:27,46-54`).
