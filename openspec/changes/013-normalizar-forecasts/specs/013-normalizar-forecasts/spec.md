# Spec — 013-normalizar-forecasts

## Criterios de aceptación

- [ ] `ForecastRegions` almacena región × período con unique_together
- [ ] `ForecastExtendedDay` almacena día extendido con unique_together
- [ ] Migración de datos: los registros existentes se migran sin pérdida
- [ ] API `/api/forecast/<date>/` devuelve misma estructura JSON (retrocompatible)
- [ ] Página principal (index) funciona igual que antes
- [ ] Dashboard CRUD (crear/editar/listar) funciona igual que antes
- [ ] Dashboard principal (charts) funciona igual que antes
- [ ] `python manage.py test` — todos los tests pasan
- [ ] `python manage.py check` — sin errores
