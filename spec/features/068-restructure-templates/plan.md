# Plan · 068 Restructure templates

### Paso 1: Crear estructura de directorios
- `templates/pages/commercial/`, `templates/pages/meteo/`, `templates/pages/core/`, `templates/pages/user_auth/`
- `templates/includes/commercial/`, `templates/includes/meteo/`, `templates/includes/core/`, `templates/includes/shared/`

### Paso 2: Mover templates por app
- commercial: customer, service, subscription, invoice, invoiceitem, contract, certificate
- meteo: forecast, warning, weatherreport, excel_json
- core: company_settings, site_config, email_recipients, maintenance
- user_auth: profile, user_list, user_form, group_list, group_form

### Paso 3: Mover includes
- modales específicos a `includes/{commercial,meteo,core}/`
- modal_delete.html y modal_pdf.html a `includes/shared/`

### Paso 4: Actualizar referencias
- `template_name` en vistas de commercial, meteo, core, user_auth
- `{% url 'dashboard:...' %}` → `{% url 'commercial:...' %}` / `{% url 'meteo:...' %}` / etc.
- `{% extends 'layouts/...' %}` y `{% include 'includes/...' %}` corregidos

### Paso 5: Verificar
- Navegación completa del dashboard funciona
- Modales de borrado y PDF funcionales
- Menú lateral actualizado
