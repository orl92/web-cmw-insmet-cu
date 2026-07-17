# 017 · Búsqueda y paginación

**Estado:** completado

## Qué hace

Agrega barra de búsqueda y paginación a todos los list views del dashboard. Actualmente solo `SubscriptionListView` tiene paginate_by; ningún list view tiene search.

## Criterios de aceptación

- [x] Mixin `SearchMixin` reutilizable creado en `common/utils.py`
- [x] Search bar en templates de listado (`includes/dashboard/search_bar.html` + `layouts/list.html`)
- [x] `paginate_by = 20` en todos los ListView (via SearchMixin)
- [x] Filtro `?q=` funciona en Customer, Service, Invoice, WeatherReport, Warnings, Publications, EmailRecipientList, Subscriptions
- [x] `python manage.py test` — 114 tests OK
