# Tasks — 063-templates-static

## paginate_by en dashboard ListViews

- [ ] `apps/dashboard/views/certificados/views.py:14` — Agregar
      `paginate_by = 20` en `CertificateListView`
- [ ] `apps/dashboard/views/estaciones/views.py:17` — Agregar
      `paginate_by = 20` en `StationListView`
- [ ] `apps/dashboard/views/clientes/views.py:21` — Agregar
      `paginate_by = 20` en `CustomerListView`
- [ ] `apps/dashboard/views/contratos/views.py:13` — Agregar
      `paginate_by = 20` en `ContractListView`
- [ ] `apps/dashboard/views/avisos/ciclones_tropicales/views.py:19` —
      Agregar `paginate_by = 20` en `TropicalCycloneListView`
- [ ] `apps/dashboard/views/avisos/tormentas/views.py:19` — Agregar
      `paginate_by = 20` en `StormWarningListView`
- [ ] `apps/dashboard/views/avisos/alertas_tempranas/views.py:19` —
      Agregar `paginate_by = 20` en `EarlyWarningListView`
- [ ] `apps/dashboard/views/municipios/views.py:17` — Agregar
      `paginate_by = 20` en `TownListView`
- [ ] `apps/dashboard/views/provincias/views.py:17` — Agregar
      `paginate_by = 20` en `ProvinceListView`
- [ ] `apps/dashboard/views/servicios/views.py:18` — Agregar
      `paginate_by = 20` en `ServiceListView`
- [ ] `apps/dashboard/views/pronosticos/views.py:56` — Agregar
      `paginate_by = 20` en `ForecastsListView`
- [ ] `apps/dashboard/views/tiempo/views.py:130` — Agregar
      `paginate_by = 20` en `WeatherReportListView`
- [ ] `apps/dashboard/views/email_recipient/views.py:22` — Agregar
      `paginate_by = 20` en `EmailRecipientListListView`

## Bloques comentados en templates

- [ ] Buscar `<!--` en `templates/pages/dashboard/` y remover bloques de
      desarrollo muertos
- [ ] Buscar `<!--` en `templates/pages/home/` y remover bloques muertos
- [ ] Buscar `<!--` en `templates/layouts/` y remover bloques muertos

## Alt text en imágenes

- [ ] Buscar `<img` sin `alt` en `templates/pages/home/` y agregar
- [ ] Buscar `<img` sin `alt` en `templates/pages/dashboard/` y agregar
- [ ] Buscar `<img` sin `alt` en `templates/layouts/` y agregar
- [ ] Buscar `<img` sin `alt` en `templates/pages/accounts/` y agregar

## Aria labels

- [ ] Revisar inputs sin `<label>` en templates de formularios
      (`templates/pages/dashboard/*/form*.html`)
- [ ] Agregar `aria-label` donde no haya label visible

## Verificación

- [ ] `python manage.py test`
- [ ] Revisar visualmente las páginas list (paginación aparece)
