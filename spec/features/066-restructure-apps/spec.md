# Feature 066 · Restructure apps

## Motivation
La app `dashboard/` concentra ~21 modelos de 5 dominios distintos (comercial, meteo, usuarios, config, core). `common/` mezcla utilidades transversales con modelos de negocio (CompanySettings, EmailRecipient). `accounts/` y `login/` son dos apps separadas para un mismo dominio. Esto dificulta mantenimiento, tests y navegación.

## Solución
Crear 4 nuevas apps con responsabilidad única y mover código legacy:

| App nueva | Origen | Contenido |
|---|---|---|
| `apps/core/` | `common/` + `dashboard/models/maintenance.py` | FileHandlerMixin, SoftDeleteModel, utils, error views, CompanySettings, SiteConfiguration, EmailRecipientList/Recipient, templatetags, context_processors, middleware, mail_send |
| `apps/user_auth/` | `accounts/` + `login/` | Profile, login/logout views, users/groups CRUD, LDAP, password management |
| `apps/meteo/` | `dashboard/models/pronosticos.py`, `dashboard/models/alertas.py`, `dashboard/models/reportes.py` | Forecasts/ForecastRegions/ForecastExtendedDay, Warning, WeatherReport |
| `apps/commercial/` | `crm/` + `billing/` + `dashboard/models/{clientes,servicios,facturas}.py` | Customer, Service, ServiceSubscription, Invoice/InvoiceItem, Contract, Certificate |

### Cambios adicionales
- Mover campo `PROVEEDOR_FACTURA` de `settings.py` a `CompanySettings.proveedor_factura`
- Eliminar apps legacy: `common`, `accounts`, `login`, `crm`, `billing`
- `managed=False` removido de todos los modelos (ya no hay DB externa)
- Reset completo: borrar DB, migraciones, recrear desde cero
- `SoftDeleteModel` se muda de `common/utils.py` a `apps/core/models.py`

## Criterios de aceptación
- `python manage.py test` pasa con >=259 tests
- `python manage.py check` sin errores
- Login/logout funcional
- CRUD comercial completo (Customer, Service, Invoice, Contract, Certificate)
- CRUD meteo completo (Forecasts, Warning, WeatherReport)
- DashboardView funcional con charts y KPIs
- API endpoints funcionales
- `CompanySettings.proveedor_factura` visible y editable en admin
