# Tasks · 071 Performance queries

## Fase 1 — Índices (del spec original)

- [ ] `apps/meteo/models.py` — `db_index` en campos filtrados (report_type, date)
- [ ] `apps/meteo/models.py` — `db_index` en Warning (warning_type, valid_until)
- [ ] `apps/commercial/models.py` — `db_index` en Invoice (issue_date)
- [ ] Auditar N+1 en list views de commercial, dashboard, meteo con `assertNumQueries`
- [ ] Agregar `select_related`/`prefetch_related` donde falte
- [ ] `python manage.py makemigrations` + `migrate`

## Fase 2 — Gaps de la auditoría (ver 092-performance-paginacion)

- [ ] API N+1: `apps/api/serializers.py:50,85` filtran/ordenan dentro del serializer → mover a `Prefetch` en vistas (StationList, WarningList, WeatherReportList, ScientificPublicationList)
- [ ] Paginación muerta: 8 listados con `context['objects']` anulan `paginate_by` → usar `page_obj` o documentar DataTables
- [ ] Context processor (~13 queries/request) → cache API con TTL
- [ ] Templatetags legacy (`meteo_filters.get_forecast_day/get_period`) → precargar en vista o cachear
- [ ] Test `assertNumQueries` estable en StationList/WarningList
