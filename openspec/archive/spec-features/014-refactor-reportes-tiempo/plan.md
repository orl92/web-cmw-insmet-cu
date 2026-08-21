# 014 · Refactor reportes meteorológicos — Plan

## Enfoque

Crear un modelo único `WeatherReport` con campo `type` (today/tomorrow/commentary/note) que reemplaza los 4 modelos individuales. Consolidar formularios, vistas y URLs en una implementación genérica parametrizada por tipo. Los 4 modelos originales se mantienen como stubs (sin cambios) para no romper migraciones existentes.

## Implementación

### 1. Modelos (`dashboard/models.py`)

- Crear `WeatherReport(FileHandlerMixin, models.Model)` con:
  - `uuid`, `user` (FK User), `date` (DateTimeField), `summary` (TextField), `file` (FileField), `email_recipient_list` (FK EmailRecipientList)
  - `type` (CharField max_length=20, choices: today/tomorrow/commentary/note)
- Meta: `default_permissions = ()` + 16 permissions custom (view/add/change/delete para cada tipo)
- Los modelos antiguos (`WeatherToday`, `WeatherTomorrow`, `WeatherCommentary`, `WeatherNote`) se mantienen intactos como stubs

### 2. Migración

- `makemigrations` crea migración para nueva tabla `dashboard_weatherreport`
- Comando `migrate_weather_reports`:
  - Copia datos de `WeatherToday` → `WeatherReport(type='today')`
  - Copia datos de `WeatherTomorrow` → `WeatherReport(type='tomorrow')`
  - Copia datos de `WeatherCommentary` → `WeatherReport(type='commentary')`
  - Copia datos de `WeatherNote` → `WeatherReport(type='note')`
  - Opcional: flag `--drop-old` para eliminar tablas viejas

### 3. Formularios (`dashboard/forms/`)

- Crear `WeatherReportForm(forms.ModelForm)`:
  - Meta.model = WeatherReport, fields = ['summary', 'file', 'email_recipient_list']
  - Acepta `report_type` y `user` en kwargs
- Eliminar las 4 carpetas de forms individuales

### 4. Vistas dashboard

- Reemplazar `dashboard/views/tiempo/hoy/views.py`, `.../manana/views.py`, `dashboard/views/comentarios/tiempo/views.py`, `.../nota_meteorologica/views.py` con un solo archivo: `dashboard/views/tiempo/views.py`
- 6 vistas genéricas parametrizadas por `report_type`:
  - `WeatherReportListView` — filtra por type, permission_required dinámico
  - `WeatherReportCreateView` — setea type + date=now
  - `WeatherReportUpdateView` — con UserPassesTestMixin (owner/superuser)
  - `WeatherReportDeleteView` — POST-only View con modal
  - `WeatherReportDetailView`
  - `WeatherReportPDFView` — genera PDF con xhtml2pdf
- Cada vista determina el `report_type` del URL kwarg y construye el nombre de permiso dinámicamente

### 5. Vistas home (`home/views/`)

- Reemplazar `home/views/tiempo/hoy/views.py`, `.../manana/views.py`, `home/views/comentarios/tiempo/views.py`, `.../nota_meteorologica/views.py` con un solo archivo: `home/views/tiempo/views.py`
- Vista genérica `WeatherReportDetailView` que filtra por type + date__date=today

### 6. URLs

- Dashboard (`dashboard/urls.py`):
  - Mantener los mismos nombres de URL y patterns
  - Pasar `report_type` como kwarg a las vistas genéricas
  - Ej: `path('tiempo/hoy/', WeatherReportListView.as_view(), {'report_type': 'today'}, name='listado_tiempo_h')`
- Home (`home/urls.py`): mismo patrón

### 7. Templates dashboard

- Mantener templates de listado, detalle y PDF individuales por ahora (refactor de templates no está en alcance)
- Las templates de crear/actualizar ya usan `pages/dashboard/tiempo/form_crear.html` y `form_actualizar.html` — se mantienen
- Solo cambiar los contextos para usar `weatherreport_list` / `weatherreport` en vez de los nombres específicos

### 8. Admin

- Registrar `WeatherReport` con `list_filter = ('type', 'date')`

### 9. Tests

- Actualizar `dashboard/tests/test_models.py`: test para WeatherReport creation con cada type
- Actualizar `dashboard/tests/test_views.py`: reemplazar tests de vistas viejas por nuevas
- Actualizar `home/tests/test_views.py`: reemplazar tests de vistas viejas
- Actualizar `api/tests/test_api.py` si aplica
- No eliminar tests de modelos viejos (siguen existiendo como stubs)

### 10. Limpieza

- `python manage.py check` — sin errores
- `python manage.py test` — todos pasan
- Actualizar roadmap.md

## Decisiones

- **Sin proxy models**: El modelo único con type field + permisos custom es más simple que proxy models. Las vistas verifican `has_perm('dashboard.view_weather_today')` dinámicamente según el type.
- **TextField para summary**: ya era TextField en WeatherToday; TextField puede contener cualquier CharField
- **date como DateTimeField manual**: en vez de auto_now_add, para consistencia entre tipos
- **Modelos viejos como stubs**: no se eliminan para no romper migraciones existentes localmente. Se eliminarán en feature futura.

## Riesgos

- **Permisos**: 16 permisos custom en un solo modelo puede ser confuso en admin. Mitigar con naming claro.
- **URLs existentes**: los nombres de URL se mantienen. Los bookmarks existentes siguen funcionando.
- **Rendimiento**: una sola tabla es más eficiente que 4 tablas separadas. Index en (type, date).
- **Código legacy**: las 4 carpetas de vistas viejas se eliminan; si alguien las importa en otro lugar, se rompe. Verificar imports cruzados.
