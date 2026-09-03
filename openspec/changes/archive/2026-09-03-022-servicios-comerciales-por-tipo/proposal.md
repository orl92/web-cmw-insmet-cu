# Proposal: Servicios Comerciales por Tipo (Categoría de Facturación)

## Intent

El flujo comercial actual tiene 5 problemas: (1) bug de permiso inexistente en AJAX de facturas, (2) staff sin botones en vista pública, (3) facturación poco visible, (4) cliente sin guía en pending sin QR, y (5) **modelo de negocio rígido** — todos los servicios usan `PERIOD_DAYS = 30` y rango libre de fechas. Se necesita soportar dos categorías de servicio: agrometeorológico (mensual) y pronóstico (diario), con facturación por cantidad de meses/días.

## Scope

### In Scope
- Campo `service_category` en `Service` (`agrometeo` | `pronostico`) con default `pronostico`
- Campo `quantity` (IntegerField) en `ServiceSubscription` para meses/días
- Cálculo de `end_date` según categoría: `start_date + quantity × período`
- Cálculo de factura: `quantity × price` (reemplaza `days_count × price`)
- Fix permiso `view_servicesubscription` → `view_subscription` en `invoices.py:445`
- Bloque staff en `commercial_public.html` con botones editar/crear
- Contador de pendientes o enlace a filtrar requested en dashboard
- Detail del servicio muestra categoría y precio por período
- Form de solicitud condicionado según categoría (meses o días, no rango libre)
- Migración: `Service` existentes reciben `service_category = 'pronostico'`

### Out of Scope
- Renovación automática de suscripciones (se adapta lógica existente, no se automatiza)
- Nuevo modelo Opción A (campo `billing_period` por servicio) — diferido
- Cambios a API REST de commercial
- Pagos en línea o integración con pasarela

## Capabilities

### New Capabilities
- `commercial-service-categories`: Categorización de servicios comerciales (agrometeo/pronostico), período derivado, cálculo de end_date e importe por cantidad

### Modified Capabilities
- `commercial-subscription-flow`: Modifica solicitudes, facturación y vista pública — cantidad en vez de rango de fechas, permisos corregidos, botones staff

## Approach

1. Agregar `service_category` con `choices` a `Service` y `quantity` a `ServiceSubscription`
2. Fix del permiso en `invoices.py:445`
3. Actualizar form de solicitud para pedir cantidad según categoría
4. Actualizar cálculo de `end_date` e `importe` en views/forms
5. Agregar bloque staff en template público
6. Agregar indicador de pendientes
7. Migración con default `pronostico`

## Affected Areas

| Area | Impact | Descripción |
|------|--------|-------------|
| `apps/commercial/models.py` | Modified | Campos `service_category` y `quantity` |
| `apps/commercial/views/invoices.py:445` | Modified | Fix permiso |
| `apps/commercial/forms/subscription.py` | Modified | Form condicionado por categoría |
| `apps/home/templates/pages/home/services/commercial_public.html` | Modified | Botones staff + guía pending |
| `apps/commercial/views/` | Modified | Cálculo end_date e importe |
| `openspec/changes/022-servicios-comerciales-por-tipo/` | New | Delta specs |

## Risks

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Migración rompe suscripciones existentes | Baja | Default `pronostico` preserva comportamiento actual |
| Conflicto de numeración | Resuelto | Cambio renombrado a `022` para no colisionar con el spec archivado `021-feedback-toasts` |

## Rollback Plan

Revertir el commit. La migración agrega campos con default, así que revertir el migration y el código restaura el estado anterior sin pérdida de datos.

## Dependencies

- Ninguna dependencia externa nueva.

## Success Criteria

- [ ] `ajax_pending_subscriptions` retorna datos (no 403) para staff autenticado
- [ ] Staff ve botones "Editar" y "Crear servicio" en `commercial_public.html`
- [ ] Servicio comercial muestra categoría y precio por mes/día en detail
- [ ] Form de solicitud pide cantidad de meses (agrometeo) o días (pronostico)
- [ ] `end_date = start_date + quantity × período` calculado correctamente
- [ ] Factura genera `importe = quantity × price`
- [ ] Todos los tests existentes pasan (`python manage.py test apps.commercial apps.home`)
