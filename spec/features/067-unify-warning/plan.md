# Plan · 067 Unify Warning model

### Paso 1: Modelo Warning
- Crear modelo en `apps/meteo/models/warning.py`
- `warning_type`, `title`, `description`, `is_active`, `cyclone_name`, `category`
- FileHandlerMixin, SoftDeleteModel, UUID
- 4 permisos custom: view_warning, add_warning, change_warning, delete_warning

### Paso 2: Forms y vistas
- `WarningForm` con fieldsets condicionales (cyclone_name/category solo si warning_type=cyclone)
- 5 vistas CRUD parametrizadas por `warning_type`
- URLs: `meteo:warning_list early`, `meteo:warning_create cyclone`, etc.

### Paso 3: Templates
- warning_list.html con DataTable
- warning_form.html con JS para mostrar/ocultar campos de ciclón
- warning_detail.html
- warning_pdf.html

### Paso 4: API
- Endpoint único `/api/warnings/?type=early`
- Serializer con `warning_type` como ChoiceField

### Paso 5: Data migration + cleanup
- Migrar datos de EarlyWarning, TropicalCyclone, StormWarning a Warning
- Eliminar modelos legacy
- Tests
