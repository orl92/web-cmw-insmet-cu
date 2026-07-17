# 017 · Búsqueda y paginación

**Estado:** planificado

## Qué hace

Agrega barra de búsqueda y paginación a todos los list views del dashboard. Actualmente solo `SubscriptionListView` tiene paginate_by; ningún list view tiene search.

## Criterios de aceptación

- [ ] Mixin `SearchMixin` reutilizable creado
- [ ] Search bar en templates de listado
- [ ] `paginate_by = 20` en todos los ListView
- [ ] Filtro `?q=` funciona en Customer, Service, Invoice, Forecasts, WeatherReport, Warnings, Publications, EmailRecipientList
- [ ] `python manage.py test` — todos pasan
