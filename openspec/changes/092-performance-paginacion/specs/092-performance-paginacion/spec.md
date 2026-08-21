## Criterios de aceptación

- [ ] API sin N+1: `assertNumQueries` estable (o Toolbar) en `StationList`, `WarningList`, `WeatherReportList`.
- [ ] Listados sin DataTables paginan (navegación por página funciona y no carga todo).
- [ ] Listados con DataTables documentan que cargan todo (sin `paginate_by` fantasma).
- [ ] Context processor con cache; counts/CompanySettings no re-consultan en cada request.
- [ ] Índices agregados y migrados.
- [ ] Templatetags legacy sin queries por llamada (o cacheados).
- [ ] `python manage.py check` y `python manage.py test` pasan.
