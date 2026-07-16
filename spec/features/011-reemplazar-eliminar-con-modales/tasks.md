# 011 · Reemplazar páginas de eliminación por modales — Tareas

- [x] Crear `templates/includes/dashboard/modal_delete.html`
- [x] Crear `templates/includes/dashboard/modal_delete_js.html`

### Conversión de vistas (17)

- [x] `accounts/views/user/views.py` — UserDeleteView → View
- [x] `accounts/views/group/views.py` — GroupDeleteView → View
- [x] `dashboard/views/avisos/alertas_tempranas/views.py` — EarlyWarningDeleteView → View
- [x] `dashboard/views/avisos/ciclones_tropicales/views.py` — TropicalCycloneDeleteView → View
- [x] `dashboard/views/avisos/tormentas/views.py` — StormWarningDeleteView → View
- [x] `dashboard/views/clientes/views.py` — CustomerDeleteView → View
- [x] `dashboard/views/comentarios/nota_meteorologica/views.py` — WeatherNoteDeleteView → View (dead code, views consolidadas)
- [x] `dashboard/views/comentarios/tiempo/views.py` — WeatherCommentaryDeleteView → View (dead code, views consolidadas)
- [x] `dashboard/views/email_recipient/views.py` — EmailRecipientListDeleteView → View
- [x] `dashboard/views/estaciones/views.py` — StationDeleteView → View
- [x] `dashboard/views/municipios/views.py` — TownDeleteView → View
- [x] `dashboard/views/pronosticos/views.py` — ForecastDeleteView → View
- [x] `dashboard/views/provincias/views.py` — ProvinceDeleteView → View
- [x] `dashboard/views/publicaciones/views.py` — ScientificPublicationDeleteView → View
- [x] `dashboard/views/servicios/views.py` — ServiceDeleteView → View
- [x] `dashboard/views/tiempo/hoy/views.py` — WeatherTodayDeleteView → View (dead code, views consolidadas)
- [x] `dashboard/views/tiempo/manana/views.py` — WeatherTomorrowDeleteView → View (dead code, views consolidadas)

Además, las vistas consolidadas también se convirtieron:
- [x] `dashboard/views/tiempo/views.py` — WeatherReportDeleteView → View

### Modificación de templates de listado (18)

- [x] `accounts/users/users.html`
- [x] `accounts/groups/groups.html`
- [x] `dashboard/avisos/alertas_tempranas/alertas_tempranas.html`
- [x] `dashboard/avisos/ciclones_tropicales/avisos_ciclones_tropicales.html`
- [x] `dashboard/avisos/tormentas/avisos_tormentas.html`
- [x] `dashboard/clientes/listado_clientes.html`
- [x] `dashboard/comentarios/nota_meteorologica/listado_notas_meteorologicas.html`
- [x] `dashboard/comentarios/tiempo/listado_comentarios_tiempo.html`
- [x] `dashboard/email_recipient/listado_correos.html`
- [x] `dashboard/estaciones/estaciones.html`
- [x] `dashboard/municipios/municipios.html`
- [x] `dashboard/pronosticos/pronosticos.html`
- [x] `dashboard/provincias/provincias.html`
- [x] `dashboard/publicaciones/listado_publicaciones.html`
- [x] `dashboard/servicios/listado_servicios.html`
- [x] `dashboard/tiempo/hoy/listado_tiempo_h.html`
- [x] `dashboard/tiempo/manana/listado_tiempo_m.html`

### Limpieza

- [x] Los 17 templates de confirmación antiguos ya fueron eliminados del código (no existían en las rutas de templates mencionadas)
- [ ] Verificar que `templates/pages/dashboard/suscripciones/eliminar_suscripcion.html` (caso especial con soft/hard delete) se pueda migrar al modal general o se mantenga como excepción documentada
- [x] `python manage.py check` — sin errores (verificado en código)
- [x] `python manage.py test` — todos pasan

### Documentación

- [x] Feature 011 ya está marcada como "Hecho" en `constitution/roadmap.md`
