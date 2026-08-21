# Plan — 062-apps-responsibility

## Estrategia

Este refactor es grande. Se divide en **features hijas** (SDD anidado):

1. **Extraer geografía**: crear `apps/geo/` con Province, Town, Station.
   Migrar datos y mantener backward compatibility con `apps.dashboard.models`
   importando desde la nueva ubicación con `__init__.py` re-export.

2. **Extraer CRM**: crear `apps/crm/` con Customer, Service,
   ServiceSubscription. Las vistas de dashboard pueden referenciar los nuevos
   modelos con imports.

3. **Extraer facturación**: crear `apps/billing/` con Invoice, InvoiceItem,
   Contract, Certificate.

4. **Extraer correos**: crear `apps/mailing/` con EmailRecipientList,
   EmailRecipient.

5. **Dashboard remanente**: mantener Forecasts, BaseWarning (y subtipos),
   WeatherReport, SiteConfiguration, CompanySettings.

## Orden recomendado

1. Crear estructura de apps hijas (apps/geo/, apps/crm/, etc.)
2. Mover modelos (uno por feature hija)
3. Mover forms y vistas gradualmente
4. Actualizar urls.py del dashboard como proxy
5. Migraciones de datos

## Riesgos

- Las migraciones de datos entre apps (mover tablas de
  `dashboard_province` a `geo_province`) requieren migraciones personalizadas
  o renombrar tablas vía `db_table`.
- Muchas vistas del dashboard dependen de modelos de `dashboard`. Cada
  import debe actualizarse.
- `related_name` cross-app puede cambiar, actualizar todas las referencias.
- Este feature es **grande** — considerar dividirlo en 4-5 features SDD
  separadas (062a, 062b, …).
