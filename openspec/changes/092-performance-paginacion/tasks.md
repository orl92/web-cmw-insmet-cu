# Tasks — 092-performance-paginacion

## API sin N+1

- [ ] Auditar `apps/api/serializers.py` (líneas 50, 85 y resto) — identificar todos los `.filter()`/`.order_by()` dentro de serializers.
- [ ] `apps/api/views.py` — Mover queryset (orden + límite) a `Prefetch` objects en `StationList`, `WarningList`, `WeatherReportList`, `ScientificPublicationList` (y las que apliquen).
- [ ] `apps/api/serializers.py` — Serializers leen relaciones ya prefetched (sin re-filtrar).
- [ ] Test `assertNumQueries` estable para StationList y WarningList (antes y después).
- [ ] Verificar orden de resultados idéntico al anterior.

## Paginación

- [ ] **Regla**: `paginate_by = 20` solo en listados SIN DataTables (paginación servidor con `page_obj`). Los listados con DataTables cargan todo y pagan en cliente (layout `layouts/list.html` inicializa `new DataTable`).
- [ ] Auditar las 13 vistas con `paginate_by`:
  - Con DataTables (extienden `layouts/list.html`): customers, services, subscriptions, invoices, certificates, contracts (commercial), forecast, warning, weather_report (meteo), email_recipients (core) → **eliminar `paginate_by` fantasma** y el `context['objects']` con queryset completo (evitar doble query).
  - Sin DataTables (paginación real con `page_obj`): home servicios comerciales/publicos (`paginate_by=10`) → **mantener y verificar** que paginan bien.
- [ ] Si algún listado futuro no usa DataTables → usar `page_obj` + `paginate_by = 20` (convención del proyecto).
- [ ] Verificar navegación de páginas en los listados sin DataTables (home servicios).

## Índices

- [ ] `apps/meteo/models.py` — `Meta.indexes` con `Index(fields=['report_type', 'date'])` en WeatherReport.
- [ ] `apps/meteo/models.py` — `Index(fields=['warning_type', 'valid_until'])` en Warning.
- [ ] `apps/commercial/models.py` — `Index(fields=['issue_date'])` en Invoice.
- [ ] `python manage.py makemigrations` + `migrate`.

## Context processor

- [ ] Auditar `apps/core/context_processors.py` (~13 queries).
- [ ] Cachear CompanySettings/SiteConfiguration/sidebar counts con cache API (TTL documentado, ej. 300s).
- [ ] Invalidar cache en save (post_save de CompanySettings/SiteConfiguration o al tocar los modelos relevantes).
- [ ] Verificar con `assertNumQueries` (o log) que el context processor no consulta por request.

## Templatetags

- [ ] Auditar `apps/meteo/templatetags/meteo_filters.py` (`get_forecast_day`, `get_period`).
- [ ] Precargar datos en la vista y pasar por context, o cachear la query.
- [ ] Verificar que los templates de home/meteo no disparan queries por llamada.

## Verificación

- [ ] `python manage.py check`
- [ ] `python manage.py test`
- [ ] `python manage.py makemigrations --check --dry-run` (limpio)
- [ ] Actualizar roadmap.md (mover 092 a Hecho al completar).
- [ ] Commit.
