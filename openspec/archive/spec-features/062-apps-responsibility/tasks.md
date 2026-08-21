# Tasks — 062-apps-responsibility

Tasks de alto nivel. Cada bloque es candidato a ser su propia feature SDD.

## Fase 1: Análisis y plan detallado

- [ ] Identificar todos los imports de `apps.dashboard.models` en views,
      forms, templates, tests y tasks
- [ ] Mapear dependencias entre modelos intra-dominio y cross-dominio
- [ ] Decidir estrategia de migración de tablas (db_table vs migraciones
      separadas)

## Fase 2: Extraer geografía → `apps/geo/`

- [ ] Crear `apps/geo/models.py` con Province, Town, Station (idéntico)
- [ ] Crear `apps/geo/urls.py` con `app_name = 'geo'`
- [ ] Crear `apps/geo/views/`, `apps/geo/forms/`, `apps/geo/tests/`
- [ ] Configurar `db_table = 'dashboard_province'` etc. para cero迁移
- [ ] Re-exportar en `apps/dashboard/models.py` para backward compat
- [ ] Migrar vistas de dashboard a `apps.geo`
- [ ] Agregar `apps.geo` a INSTALLED_APPS

## Fase 3: Extraer CRM → `apps/crm/`

- [ ] Crear `apps/crm/models.py` con Customer, Service, ServiceSubscription
- [ ] Migrar forms y vistas relacionadas
- [ ] Re-exportar en dashboard para compat

## Fase 4: Extraer facturación → `apps/billing/`

- [ ] Crear `apps/billing/models.py` con Invoice, InvoiceItem, Contract,
      Certificate
- [ ] Migrar forms y vistas

## Fase 5: Extraer correos → `apps/mailing/`

- [ ] Crear `apps/mailing/models.py` con EmailRecipientList, EmailRecipient
- [ ] Migrar forms y vistas

## Fase 6: Limpieza

- [ ] Remover re-exports de dashboard/models.py
- [ ] Actualizar `config/urls.py`
- [ ] Verificar todos los templates referencian las URLs correctas
- [ ] `python manage.py test`
