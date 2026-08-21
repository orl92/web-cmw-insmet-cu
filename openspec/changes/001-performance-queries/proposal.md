# 071 — performance-queries

## Motivación

Las list views de `commercial/` usan `select_related` en algunos casos pero no todos. `DashboardView` hace varias queries que pueden tener N+1. Faltan índices en columnas frecuentemente filtradas.

## Alcance

- Auditar N+1 en todas las list views de commercial, dashboard, meteo
- Agregar `select_related`/`prefetch_related` donde falte
- Agregar `db_index=True` en campos frecuentes: `is_active`, `issue_date`, `payment_status`, `service_type`

## Criterios de Aceptación

1. Ninguna list view produce más de 10 queries (medido con `assertNumQueries`)
2. Migraciones añaden índices sin romper existente
3. `python manage.py test` pasa
