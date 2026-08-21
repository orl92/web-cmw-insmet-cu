# Feature 092 · Performance y paginación

## Motivación

Auditoría de rendimiento encontró problemas medibles en listados, API y contexto global:

1. **Prefetch roto → N+1 en la API** — `apps/api/serializers.py:50,85` usan `.filter()`/`.order_by()` dentro de serializers sobre relaciones. Eso invalida `prefetch_related` de la vista: Django re-ejecuta una query por registro. Afecta: `StationSerializer.observations` (línea 50), `WarningSerializer.forecasts` o similar (línea 85), y vistas relacionadas (`StationList`, `WarningList`, `WeatherReportList`, `ScientificPublicationList`).
2. **Paginación muerta en listados** — 13 vistas declaran `paginate_by` (20 o 10) pero la mayoría extienden `layouts/list.html`, que SIEMPRE inicializa DataTable (paginación cliente sobre queryset completo) e itera `context['objects']`. Resultado: `paginate_by` es código muerto + **doble query** (queryset completo + queryset paginado). Solo 2 vistas (home servicios públicos/comerciales) usan paginación servidor real con `page_obj` sobre templates sin DataTables.
   - **Regla a aplicar**: `paginate_by = 20` SOLO en listados SIN DataTables (paginación servidor con `page_obj`). Listados con DataTables cargan todo y pagan en cliente (AGENTS.md).
3. **Context processor caro** — `apps/core/context_processors.py` ejecuta ~13 queries por request (todas las vistas): sidebar con counts, CompanySettings, SiteConfiguration, etc. Sin cache y sin índices en las tablas consultadas.
4. **Faltan índices** — `WeatherReport(report_type, date)`, `Warning(warning_type, valid_until)`, `Invoice(issue_date)` (o los campos usados en filtros/ordenamientos frecuentes).
5. **Templatetags legacy con queries** — `apps/meteo/templatetags/meteo_filters.py` (`get_forecast_day`, `get_period`) hacen queries por llamada en los templates.

## Solución

### 1. Prefetch / N+1 API
- Reemplazar `.filter()`/`.order_by()` en serializers por:
  - `Prefetch` objects en las vistas (`prefetch_related(Prefetch('observations', queryset=...))`), o
  - `SerializerMethodField` con `self.context['request']` y queryset ya prefetched, o
  - Annotations/subqueries (`Subquery`) cuando aplique.
- Mantener el orden y el límite en el queryset del Prefetch, NO en el serializer.
- Verificar con `django-debug-toolbar` o `assertNumQueries` que N+1 desaparece.

### 2. Paginación
- Auditar las 8 vistas: las que usan DataTables (cargar todo intencionalmente) → quitar `paginate_by` si está de más o documentar; las que NO usan DataTables → usar `page_obj` en el template y eliminar `context['objects']` (o pasar `object_list` correctamente paginado).
- Eliminar la doble query.

### 3. Context processor
- Auditar las ~13 queries: cachear con `django.core.cache` (cache API o template fragment caching) los valores que cambian poco (CompanySettings, SiteConfiguration, sidebar counts).
- Documentar el TTL.

### 4. Índices
- Agregar `db_index=True` (o `Meta.indexes` con `Index(fields=[...])`) a los campos filtrados/ordenados frecuentemente.
- `makemigrations` + `migrate`.

### 5. Templatetags
- Si `get_forecast_day`/`get_period` consultan por llamada, mover a un único queryset precargado en la vista y pasarlo por context, o cachear.

## Criterios de aceptación

- [ ] API sin N+1: `assertNumQueries` estable (o Toolbar) en `StationList`, `WarningList`, `WeatherReportList`.
- [ ] Listados sin DataTables paginan (navegación por página funciona y no carga todo).
- [ ] Listados con DataTables documentan que cargan todo (sin `paginate_by` fantasma).
- [ ] Context processor con cache; counts/CompanySettings no re-consultan en cada request.
- [ ] Índices agregados y migrados.
- [ ] Templatetags legacy sin queries por llamada (o cacheados).
- [ ] `python manage.py check` y `python manage.py test` pasan.
