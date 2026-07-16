# 014 · Refactor reportes meteorológicos — Tareas

### Modelos

- [x] Crear `WeatherReport(FileHandlerMixin, models.Model)` en `dashboard/models.py` con campos: uuid, user, date, summary (TextField), file, email_recipient_list, type (choices: today/tomorrow/commentary/note)
- [x] Definir `Meta.default_permissions = ()` + 16 permisos custom (4 por tipo)
- [x] `makemigrations` y `migrate`

### Migración de datos

- [x] Crear management command `migrate_weather_reports` que copia datos de las 4 tablas viejas a `WeatherReport` con type adecuado

### Formularios

- [x] Crear `dashboard/forms/tiempo/forms.py` con `WeatherReportForm(forms.ModelForm)` que acepta `report_type` y `user` en kwargs
- [ ] Los forms antiguos (`dashboard/forms/tiempo/hoy/`, etc.) son dead code — pendiente de limpieza

### Vistas dashboard

- [x] Crear `dashboard/views/tiempo/views.py` con 6 vistas genéricas (ListView, CreateView, UpdateView, DeleteView, DetailView, PDFView) parametrizadas por `report_type`
- [x] Construir `permission_required` dinámicamente según el type
- [x] `WeatherReportDeleteView`: View POST-only con modal
- [x] `WeatherReportPDFView`: generar PDF con xhtml2pdf
- [ ] Las vistas antiguas (`dashboard/views/tiempo/hoy/`, etc.) son dead code — pendiente de limpieza
- [x] `mail_send` funciona con WeatherReport

### Vistas home

- [x] Crear `home/views/tiempo/views.py` con `WeatherReportDetailView` genérica
- [ ] Las vistas antiguas (`home/views/tiempo/hoy/`, etc.) son dead code — pendiente de limpieza

### URLs

- [x] Actualizar `dashboard/urls.py`: mantener los mismos patterns y names, apuntar a vistas genéricas con `{'report_type': ...}`
- [x] Actualizar `home/urls.py`: mismo patrón
- [x] Añadir URL patterns para detalle y PDF de commentary y note
- [x] Verificar enlaces del menú y de templates

### Admin

- [x] Registrar `WeatherReport` en `dashboard/admin.py` con `list_filter = ('type', 'date')`

### Templates dashboard

- [x] Crear templates de detalle faltantes (4 templates: hoy, mañana, comentario, nota)
- [ ] Templates de PDF pendientes (Feature 015)
- [x] Templates de listado funcionan con context_object_name del REPORT_CONFIG

### Templates home

- [x] Templates públicas funcionan con el nuevo modelo (vista genérica filtra por type + date)

### Tests

- [ ] Tests existentes en stubs — Feature 012 los expandirá

### Limpieza

- [x] `python manage.py check` — sin errores
- [ ] Los directorios de vistas/forms antiguos son dead code — limpieza opcional (no rompe funcionalidad)
- [x] Actualizar roadmap.md
