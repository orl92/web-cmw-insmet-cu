# Tasks · 001-performance-queries

## Phase 1 — API N+1 elimination (`apps/api/views.py`)

- [x] `StationListAPIView.queryset` (line 104): `Station.objects.select_related('province')` (serializer reads `province.code/name`).
- [x] `EarlyWarningListAPIView.get_queryset` (lines 147-148): `.select_related('user')` appended.
- [x] `TropicalCycloneListAPIView.get_queryset` (lines 155-156): `.select_related('user')` appended.
- [x] `StormWarningListAPIView.get_queryset` (lines 165-166): `.select_related('user')` appended.
- [x] `WeatherReportListAPIView.get_queryset` (lines 173-177): `.select_related('user')` appended.
- [x] `ScientificPublicationListAPIView.queryset` (line 181): `ScientificPublication.objects.select_related('author').prefetch_related('coauthors')`.
- [x] `ForecastAPIView` (line 125) and `ServiceListAPIView` (lines 186-189): verified no change required (already optimized / no relation access).

## Phase 2 — meteo HTML view fix (`apps/meteo/views/warning.py`)

- [x] `WarningListView.get_queryset` (lines 90-91): changed to `Warning.objects.select_related('user').filter(warning_type=self.get_warning_type())`. NOTE: only `'user'` is joined. The actual template rendered by this view is `apps/meteo/templates/pages/meteo/warning/early_warning/list.html` (extends `layouts/list.html`, a DataTables grid) which reads `object.user.get_full_name` (line 26) — it does NOT read `user.profile`. The `user__profile` reference in the design points to `templates/layouts/avisos.html`, which is a CARD layout used only by the public home warning pages (`apps/home/.../warnings/*.html`), NOT by this view. Those home views are out of scope (proposal Scope Out).
- [x] `WarningListView.get_context_data` (line 103): **Evaluated — NOT modified.** This view renders a DataTables grid that loads ALL records and paginates client-side (project convention). Replacing `context['objects']` with `page_obj` would break client-side pagination; the full-queryset override is the correct behavior. No change required.
- [x] `templates/layouts/avisos.html`: **Evaluated — NOT modified.** `avisos.html` is a card layout extended only by the public home warning pages (`apps/home/.../warnings/*.html`), whose views do not provide `page_obj`; the pagination include is not applicable there. Out of scope (home). The meteo `WarningListView` uses `layouts/list.html` (DataTables), not `avisos.html`.

## Phase 3 — Query instrumentation (`assertNumQueries`)

- [x] `apps/api/tests/test_api.py`: added `assertNumQueries` cases covering every Phase 1 endpoint. Calibrated counts (this env, incl. `SiteConfiguration` middleware query): station=2, each warning endpoint=2, weather-report=2, publication=3, forecast=8. The design's predicted 1/1/1/2/3 omitted the constant `MaintenanceModeMiddleware` `SiteConfiguration.objects.first()` query; the exact calibrated constants are used as regression guards (constant → catches N+1 if a join is dropped).
- [x] `apps/meteo/tests/test_performance.py`: added `WarningListViewQueryCountTests` asserting a bounded query count (14) and that the DataTables view loads all 25 records (client-side pagination). Joins `user` via `select_related`.
- [x] Run `python manage.py test apps.api apps.meteo` → 52 tests pass.

## Phase 4 — Verification

- [x] `python manage.py check` passes (0 issues).
- [x] `python manage.py test apps.api apps.meteo` passes (52 tests).
- [x] Commit under the change number/name (committed after verify/archive).
