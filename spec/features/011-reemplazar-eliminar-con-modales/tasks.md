# 011 · Reemplazar páginas de eliminación por modales — Tareas

- [ ] Crear `templates/includes/dashboard/modal_delete.html`
- [ ] Crear `templates/includes/dashboard/modal_delete_js.html`

### Conversión de vistas (17)

- [ ] `accounts/views/user/views.py` — UserDeleteView → View
- [ ] `accounts/views/group/views.py` — GroupDeleteView → View
- [ ] `dashboard/views/avisos/alertas_tempranas/views.py` — EarlyWarningDeleteView → View
- [ ] `dashboard/views/avisos/ciclones_tropicales/views.py` — TropicalCycloneDeleteView → View
- [ ] `dashboard/views/avisos/tormentas/views.py` — StormWarningDeleteView → View
- [ ] `dashboard/views/clientes/views.py` — CustomerDeleteView → View
- [ ] `dashboard/views/comentarios/nota_meteorologica/views.py` — WeatherNoteDeleteView → View
- [ ] `dashboard/views/comentarios/tiempo/views.py` — WeatherCommentaryDeleteView → View
- [ ] `dashboard/views/email_recipient/views.py` — EmailRecipientListDeleteView → View
- [ ] `dashboard/views/estaciones/views.py` — StationDeleteView → View
- [ ] `dashboard/views/municipios/views.py` — TownDeleteView → View
- [ ] `dashboard/views/pronosticos/views.py` — ForecastDeleteView → View
- [ ] `dashboard/views/provincias/views.py` — ProvinceDeleteView → View
- [ ] `dashboard/views/publicaciones/views.py` — ScientificPublicationDeleteView → View
- [ ] `dashboard/views/servicios/views.py` — ServiceDeleteView → View
- [ ] `dashboard/views/tiempo/hoy/views.py` — WeatherTodayDeleteView → View
- [ ] `dashboard/views/tiempo/manana/views.py` — WeatherTomorrowDeleteView → View

### Modificación de templates de listado (17)

- [ ] `accounts/users/users.html`
- [ ] `accounts/groups/groups.html`
- [ ] `dashboard/avisos/alertas_tempranas/alertas_tempranas.html`
- [ ] `dashboard/avisos/ciclones_tropicales/avisos_ciclones_tropicales.html`
- [ ] `dashboard/avisos/tormentas/avisos_tormentas.html`
- [ ] `dashboard/clientes/listado_clientes.html`
- [ ] `dashboard/comentarios/nota_meteorologica/listado_notas_meteorologicas.html`
- [ ] `dashboard/comentarios/tiempo/listado_comentarios_tiempo.html`
- [ ] `dashboard/email_recipient/listado_correos.html`
- [ ] `dashboard/estaciones/estaciones.html`
- [ ] `dashboard/municipios/municipios.html`
- [ ] `dashboard/pronosticos/pronosticos.html`
- [ ] `dashboard/provincias/provincias.html`
- [ ] `dashboard/publicaciones/listado_publicaciones.html`
- [ ] `dashboard/servicios/listado_servicios.html`
- [ ] `dashboard/tiempo/hoy/listado_tiempo_h.html`
- [ ] `dashboard/tiempo/manana/listado_tiempo_m.html`

### Limpieza

- [ ] Eliminar los 17 templates de confirmación antiguos
- [ ] Ejecutar `python manage.py check` — sin errores
- [ ] Ejecutar `python manage.py test` — todos pasan

### Documentación

- [ ] Mover feature 011 a "Hecho" en `constitution/roadmap.md`
