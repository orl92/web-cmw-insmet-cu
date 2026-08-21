# Feature 068 · Restructure templates

## Motivation
Todos los templates del dashboard están en `templates/pages/dashboard/` ~50 archivos planos. Los includes están en `templates/includes/dashboard/` mezclando modales de commercial, meteo y core. Al crearse las apps `commercial/`, `meteo/` y `core/`, los templates deben migrarse a sus respectivas apps para mantener cohesión.

## Solución

### Estructura nueva
```
templates/
├── layouts/          # base.html, sidebar, navbar (sin cambios)
├── includes/
│   ├── shared/       # modal_delete.html, modal_pdf.html (cross-app)
│   ├── commercial/   # includes específicos de commercial
│   ├── meteo/        # includes específicos de meteo
│   └── core/         # includes de core/config
├── pages/
│   ├── commercial/   # customer_list, service_form, invoice_detail, etc.
│   ├── meteo/        # forecast_list, warning_form, weatherreport_detail, etc.
│   ├── core/         # company_settings, site_config, email_recipients, etc.
│   ├── user_auth/    # profile, user_list, login, etc.
│   ├── dashboard/    # solo dashboard.html (la vista principal)
│   ├── home/         # (sin cambios)
│   ├── api/          # (sin cambios)
│   └── publications/ # (sin cambios)
```

### Trabajo concreto
- Mover templates de `pages/dashboard/facturacion/` → `pages/commercial/`
- Mover templates de `pages/dashboard/contratos/` → `pages/commercial/`
- Mover templates de `pages/dashboard/certificados/` → `pages/commercial/`
- Mover templates de `pages/dashboard/pronosticos/` → `pages/meteo/`
- Mover templates de `pages/dashboard/alertas/` → `pages/meteo/`
- Mover templates de `pages/dashboard/reportes/` → `pages/meteo/`
- Mover templates de `pages/dashboard/configuracion/` → `pages/core/`
- Mover templates de `pages/dashboard/accounts/` → `pages/user_auth/`
- Mover includes de `includes/dashboard/` → `includes/{commercial,meteo,core}/`
- `includes/shared/modal_delete.html` y `includes/shared/modal_pdf.html` para uso cross-app
- Actualizar todos los `{% url 'dashboard:...' %}` en templates al nuevo namespace
- Actualizar `template_name` en todas las vistas de commercial, meteo, core, user_auth
- Corregir `extends` paths

### Modales cross-app
El `modal_delete.html` y `modal_pdf.html` se usan desde múltiples apps. Van en `includes/shared/` y se cargan con `{% include 'includes/shared/modal_pdf.html' %}`.
