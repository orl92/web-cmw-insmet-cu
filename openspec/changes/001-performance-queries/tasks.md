# Tasks · 001-performance-queries

## Phase 1 — API N+1 elimination (`apps/api/views.py`)

- [ ] `StationListAPIView.queryset` (line 104): change `Station.objects.all()` → `Station.objects.select_related('province')` (serializer reads `province.code/name`, `apps/api/serializers.py:18-19`).
- [ ] `EarlyWarningListAPIView.get_queryset` (lines 147-148): append `.select_related('user')` (serializer reads `user.username`, `apps/api/serializers.py:105`).
- [ ] `TropicalCycloneListAPIView.get_queryset` (lines 155-156): append `.select_related('user')`.
- [ ] `StormWarningListAPIView.get_queryset` (lines 165-166): append `.select_related('user')`.
- [ ] `WeatherReportListAPIView.get_queryset` (lines 173-177): append `.select_related('user')` (serializer reads `user.username`, `apps/api/serializers.py:113`).
- [ ] `ScientificPublicationListAPIView.queryset` (line 181): change to `ScientificPublication.objects.select_related('author').prefetch_related('coauthors')` (serializer reads `author.__str__`, `coauthors` M2M, `apps/api/serializers.py:121-122`).
- [ ] `ForecastAPIView` (line 125) and `ServiceListAPIView` (lines 186-189): no change (already optimized / no relation access).

## Phase 2 — meteo HTML view fix (`apps/meteo/views/warning.py`)

- [ ] `WarningListView.get_queryset` (lines 90-91): change to `Warning.objects.select_related('user', 'user__profile').filter(warning_type=self.get_warning_type())` (template reads `warning.user.profile.get_avatar`, `warning.user.get_full_name` — `templates/layouts/avisos.html:48,50`).
- [ ] `WarningListView.get_context_data` (line 103): stop overriding with the full queryset; expose the paginated page so server-side pagination applies, e.g. `context['objects'] = context['page_obj']`.
- [ ] `templates/layouts/avisos.html`: include the pagination partial (`{% include 'includes/pagination.html' %}`, partial consumes `page_obj` per `templates/includes/pagination.html:1-23`). `avisos.html` is a card layout (no DataTables), so pagination is server-side.

## Phase 3 — Query instrumentation (`assertNumQueries`)

- [ ] `apps/api/tests/test_api.py`: add `assertNumQueries` cases (station=1, warning=1, weather-report=1, publication=2, forecast=3) covering the endpoints from Phase 1.
- [ ] `apps/meteo/tests/test_performance.py` (or extend `test_warning_views.py`): add a `TestCase` asserting `WarningListView` uses a bounded query count (COUNT + 1 page, joined `user`/`user__profile`) after the Phase 2 fix.
- [ ] Run `python manage.py test apps.api apps.meteo` and confirm all new + existing tests pass.

## Phase 4 — Verification

- [ ] `python manage.py check` passes.
- [ ] `python manage.py test apps.api apps.meteo` passes (full label, Django 5.2 — see `AGENTS.md`).
- [ ] Mark every completed task `[x]` and commit under the change number/name.
