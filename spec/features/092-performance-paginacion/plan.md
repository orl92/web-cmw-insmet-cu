# 092 · Performance y paginación — Plan

## Enfoque

5 frentes de rendimiento. El más delicado es el N+1 de la API (cambia la estructura de querysets). La paginación requiere auditar vista por vista. Orden: API N+1 → paginación → índices → context processor → templatetags.

## Implementación

1. **API N+1** — para cada serializer con `.filter()`/`.order_by()`:
   - Mover el queryset (orden + límite) a un `Prefetch` en la vista.
   - El serializer usa `source`/`many=True` sin filtrar (o `SerializerMethodField` que lee `self.instance.observations.all()` ya prefetched).
   - Verificar con `assertNumQueries` en tests.
2. **Paginación** — auditar las 8 vistas:
   - Con DataTables → cargar todo (intencional), eliminar `paginate_by` fantasma.
   - Sin DataTables → `Paginator`/`ListView.paginate_by` real y template con `page_obj`; quitar `context['objects']`.
   - Eliminar la query extra.
3. **Índices** — `Meta.indexes` (o `db_index`) para `WeatherReport(report_type, date)`, `Warning(warning_type, valid_until)`, `Invoice(issue_date)`; migrar.
4. **Context processor** — cache API con TTL (ej. 300s) para CompanySettings/SiteConfiguration/sidebar counts; invalidar en save (post_save signal) si es fácil, o aceptar TTL.
5. **Templatetags** — precargar datos en la vista y pasar por context, o cachear la query.

## Riesgos

- Mover queryset a Prefetch cambia el orden si el serializer hoy ordena dentro: asegurar que el Prefetch respeta el orden original.
- `assertNumQueries` puede variar por BD; usar un test específico no la suite entera.
- Cache de CompanySettings/SiteConfiguration: invalidar en el save para no mostrar valores viejos en admin; riesgo bajo.
- La paginación en vistas DataTables es intencional según AGENTS.md: NO convertir DataTables a paginación servidor (fuera de alcance).

## Verificación

- `python manage.py check`
- `python manage.py test`
- Test específico: `assertNumQueries` en StationList/WarningList.
- Manual: listado sin DataTables pagina; listado con DataTables sigue funcionando.
- `python manage.py makemigrations --check --dry-run` (sin cambios pendientes).
