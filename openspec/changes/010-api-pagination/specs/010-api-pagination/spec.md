# api-pagination Specification

## Purpose

Define how DRF list endpoints paginate responses: a global `PageNumberPagination`
envelope (`count`, `next`, `previous`, `results`) with `PAGE_SIZE=50`, while
exempting `StationListAPIView` (flat array for `map_station.js`) and detail
endpoints (single object). drf-spectacular must reflect pagination automatically.

## Requirements

### Requirement: Global DRF Pagination Configuration

The `REST_FRAMEWORK` dict in `config/settings.py` MUST define
`DEFAULT_PAGINATION_CLASS = 'rest_framework.pagination.PageNumberPagination'`
and `PAGE_SIZE = 50`. This applies to every `ListAPIView` unless overridden.

#### Scenario: Global pagination is enabled

- GIVEN the Django settings are loaded
- WHEN `settings.REST_FRAMEWORK` is inspected
- THEN `DEFAULT_PAGINATION_CLASS` SHALL equal `'rest_framework.pagination.PageNumberPagination'`
- AND `PAGE_SIZE` SHALL equal `50`

### Requirement: Station List Stays Unpaginated

`StationListAPIView` (`apps/api/views.py`) MUST set `pagination_class = None` so
`/api/stations/` returns a flat JSON array, preserving `map_station.js:62-68`
(`data.forEach`).

#### Scenario: Stations endpoint returns a flat array

- GIVEN at least one station exists
- WHEN a client GETs `/api/stations/`
- THEN the response body SHALL be a JSON array (no `results` key)
- AND `response.data` SHALL NOT contain `count`, `next`, or `previous`

### Requirement: Paginated List Envelope

The list endpoints `EarlyWarningListAPIView`, `TropicalCycloneListAPIView`,
`StormWarningListAPIView`, `WeatherReportListAPIView`,
`ScientificPublicationListAPIView`, and `ServiceListAPIView` MUST return the
envelope `{count, next, previous, results}` with at most `PAGE_SIZE` items per
page.

#### Scenario: Affected list endpoint returns envelope

- GIVEN more than 50 records exist for an affected list endpoint
- WHEN a client GETs its list URL without `?page=`
- THEN `response.data` SHALL contain `count`, `next`, `previous`, `results`
- AND `len(response.data['results'])` SHALL be `<= 50`

#### Scenario: Second page is reachable

- GIVEN more than 50 records exist
- WHEN a client GETs the list URL with `?page=2`
- THEN `response.data['results']` SHALL contain the next slice
- AND `response.data['previous']` SHALL not be `null`

### Requirement: OpenAPI Reflects Pagination

drf-spectacular MUST document the paginated envelope in `/api/schema/` and
`/api/doc/` without manual schema edits, because
`DEFAULT_PAGINATION_CLASS` is set globally.

#### Scenario: Schema exposes pagination fields

- GIVEN the OpenAPI schema is generated via `/api/schema/`
- WHEN a client fetches the schema for an affected list endpoint
- THEN the response component SHALL include `count`, `next`, `previous`, `results`
- AND `StationListAPIView` SHALL be documented as a plain array

### Requirement: Detail Endpoints Are Not Paginated

`StationObservationView` and `ForecastAPIView` (`GenericAPIView` detail views)
MUST NOT paginate and SHALL return a single object.

#### Scenario: Forecast detail returns a single object

- GIVEN a forecast exists for a given date
- WHEN a client GETs `/api/forecast/<date>/`
- THEN `response.data` SHALL NOT contain `results`
- AND `response.data` SHALL be a single object (the forecast)

#### Scenario: Station observation returns a single object

- GIVEN station observations exist
- WHEN a client GETs the station observation detail URL
- THEN `response.data` SHALL NOT contain `results`
- AND `response.data` SHALL be a single object

### Requirement: No Internal Frontend Regression

`static/dist/js/map_station.js` (expects flat station array) and
`static/dist/js/home-forecast.js` (consumes forecast detail object) MUST
continue working unchanged after pagination is enabled.

#### Scenario: map_station.js data shape preserved

- GIVEN `/api/stations/` returns a flat array (REQ-2)
- WHEN `map_station.js` runs `data.forEach`
- THEN iteration SHALL succeed with no `results` access error

#### Scenario: home-forecast.js detail shape preserved

- GIVEN `/api/forecast/<date>/` returns a single object (REQ-5)
- WHEN `home-forecast.js` reads forecast fields directly
- THEN field access SHALL succeed with no `results` unwrap
