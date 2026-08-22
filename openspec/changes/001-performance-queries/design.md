# Design: Optimize ORM query performance for `meteo` API and views

## 1. Problem statement

The `apps/api` DRF list endpoints and one `apps/meteo` HTML list view traverse
model relations inside serializers / templates without pre-joining those
relations, producing N+1 query patterns. Separately, one HTML list view sets
`paginate_by` yet overrides the context with the full queryset, so the intended
server-side pagination never executes. None of this is currently guarded by
tests, so it can regress silently.

## 2. Current state (verified, with `file:line`)

### 2.1 API endpoints (`apps/api/views.py`, serializers in `apps/api/serializers.py`)

| Endpoint | Queryset (file:line) | Relation walked in serializer | Defect |
|---|---|---|---|
| `StationListAPIView` | `Station.objects.all()` — `views.py:104` | `province.code`, `province.name` — `serializers.py:18-19` | N+1 on `Province` |
| `EarlyWarningListAPIView` | `MeteoWarning.objects.filter(...)` — `views.py:147-148` | `user.username` — `serializers.py:105` | N+1 on `User` |
| `TropicalCycloneListAPIView` | `views.py:155-156` | `user.username` — `serializers.py:105` | N+1 on `User` |
| `StormWarningListAPIView` | `views.py:165-166` | `user.username` — `serializers.py:105` | N+1 on `User` |
| `WeatherReportListAPIView` | `WeatherReport.objects.filter(...)` — `views.py:173-177` | `user.username` — `serializers.py:113` | N+1 on `User` |
| `ScientificPublicationListAPIView` | `ScientificPublication.objects.all()` — `views.py:181` | `author.__str__`, `coauthors` (M2M) — `serializers.py:121-122` | N+1 on `Author` + N+1 on `coauthors` |
| `ForecastAPIView` | `Forecasts.objects.prefetch_related('regions','extended_days')` — `views.py:125` | `obj.regions.filter(...)` ×3, `obj.extended_days...` — `serializers.py:50,85` | **No N+1** — prefetch cache is reused; serializer re-filters the cache in Python |
| `ServiceListAPIView` | `Service.objects.filter(service_type='public')` — `views.py:186-189` | none (scalar fields only) | None |

Model relations confirmed: `Station.province` FK (`apps/meteo/models.py:385`);
`Warning.user` FK (`apps/meteo/models.py:291`);
`WeatherReport.user` FK (`apps/meteo/models.py:230`);
`ScientificPublication.author` FK + `coauthors` M2M (`apps/publications/models.py:12-20`).

### 2.2 meteo HTML views (`apps/meteo/views/`)

| View | Queryset / relation | Pagination | Defect |
|---|---|---|---|
| `WarningListView` | `Warning.objects.filter(warning_type=...)` — `warning.py:90-91`; template reads `warning.user.profile.get_avatar`, `warning.user.get_full_name` — `templates/layouts/avisos.html:48,50` | `paginate_by = 20` (`warning.py:74`) but `context['objects'] = self.get_queryset()` (`warning.py:103`); `avisos.html` is a card layout with **no** `new DataTable` | N+1 on `User` + `Profile`; **dead server-side pagination** |
| `StationListView` | `select_related('province')` — `station.py:31` | extends `layouts/list.html` (DataTables) | Correct by convention |
| `WeatherReportListView` | `select_related('user')` — `weather_report.py:152` | extends `layouts/list.html` (DataTables) | Correct by convention |
| `ForecastsListView` | `prefetch_related('regions','extended_days')` — `forecast.py:97` | extends `layouts/list.html` (DataTables) | Correct by convention |

`Profile.user` is `OneToOneField(User, related_name='profile')`
(`apps/user_auth/models.py:20`), so `select_related('user__profile')` is valid.

### 2.3 Instrumentation gap

A repository-wide search for `assertNumQueries` returns **zero matches** — there
is currently no regression guard for query counts anywhere.

## 3. Target state

- Every list endpoint joins its accessed relations up front; a request for N
  rows issues O(1) queries, not O(N).
- `WarningListView` emits exactly the rows for the current page and the template
  renders the standard pagination control.
- A new test suite asserts bounded query counts, locking the above in.

## 4. Implementation plan

### 4.1 API (`apps/api/views.py`)

```python
# StationListAPIView
queryset = Station.objects.select_related('province')

# EarlyWarningListAPIView / TropicalCycloneListAPIView / StormWarningListAPIView
def get_queryset(self):
    return MeteoWarning.objects.select_related('user').filter(
        warning_type='<type>', valid_until__gte=timezone.now())

# WeatherReportListAPIView
def get_queryset(self):
    report_type = self.kwargs.get('type')
    if report_type not in ALLOWED_REPORT_TYPES:
        return WeatherReport.objects.none()
    return WeatherReport.objects.select_related('user').filter(report_type=report_type)

# ScientificPublicationListAPIView
queryset = ScientificPublication.objects.select_related('author').prefetch_related('coauthors')
```

`ForecastAPIView` and `ServiceListAPIView` are left unchanged.

### 4.2 meteo HTML (`apps/meteo/views/warning.py`)

```python
def get_queryset(self):
    return Warning.objects.select_related('user', 'user__profile').filter(
        warning_type=self.get_warning_type())

def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    # do NOT replace objects with the full queryset; keep the paginated page
    context['objects'] = context['page_obj']   # iterable + exposes pagination
    ...
```

Then add the pagination partial to `templates/layouts/avisos.html`, e.g. near the
end of the list:
`{% include 'includes/pagination.html' %}` (the partial already consumes
`page_obj`, see `templates/includes/pagination.html:1-23`). Because `page_obj` is
itself iterable, `{% for warning in objects %}` keeps working unchanged.

### 4.3 Instrumentation (tests)

Add to `apps/api/tests/test_api.py` (reuse existing `StationListAPITests`,
`ForecastAPITests` setup; add warning / weather-report / publication API cases):

```python
def test_station_list_query_count(self):
    with self.assertNumQueries(1):   # stations joined with province
        self.client.get(self.url)
```

Add `apps/meteo/tests/test_performance.py` (or extend `test_warning_views.py`):

```python
def test_warning_list_query_count(self):
    self.client.force_login(self.admin)
    url = reverse('meteo:alerta_temprana_list')
    with self.assertNumQueries(2):   # 1 COUNT + 1 paginated page (joined user/profile)
        self.client.get(url)
```

Expected bounds (calibrate when authoring the tests):
- Station API: **1** (joined province).
- Warning / WeatherReport API: **1** (joined user).
- ScientificPublication API: **2** (author join + coauthors prefetch).
- Forecast API: **3** (forecast + regions prefetch + extended_days prefetch) — already.
- WarningListView (paginated): **2** (COUNT + page, joined user/profile) vs. N+1
  before.

## 5. Optional enhancements (not required for acceptance)

- `ForecastAPIView`: replace the in-Python triple `obj.regions.filter(...)` with a
  single explicit `Prefetch('regions', queryset=ForecastRegions.objects.order_by('period_order'), to_attr='prefetched_regions')` in `views.py:125`, and have
  `ForecastSerializer` read `obj.prefetched_regions`. Removes the redundant
  per-region re-filtering while keeping the query count at 3.
- Consider DRF pagination (`pagination_class`) for the API list endpoints if
  large payloads are expected; out of scope for this change.

## 6. Risks & mitigations

- **Test query-count brittleness:** Django may emit extra queries for permissions,
  sessions, or `SiteConfiguration` lookups depending on middleware. Mitigate by
  asserting an *upper bound* with a small tolerance, and by running the request
  through the real `APITestCase` / `TestCase` client so middleware matches prod.
- **`page_obj` as `objects`:** `page_obj` is iterable, so `{% for warning in objects %}`
  continues to work; the only behavioural change is that it now yields one page.
- **No migrations:** only `select_related` / `prefetch_related` and a template
  include are touched — zero schema impact, zero rollback risk.

## 7. Verification

```bash
source .venv/bin/activate
python manage.py check
python manage.py test apps.api apps.meteo
```
