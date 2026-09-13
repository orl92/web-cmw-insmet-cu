# Proposal: Layout Cards Servicios

## Intent

El usuario comparó los cards del catálogo público y Mis Servicios con el detalle (`service_detail.html` L25-32) y pidió alinearlos. El patrón del detalle usa `<div class="mb-2">` por línea con icono `me-1` + label + `<strong>` y precio `text-primary` destacado. Los cards actuales apiñan metadata en un solo `<div class="d-flex flex-wrap gap-2">`.

## Alcance

**Dentro (3 frentes, 2 templates, 0 backend):**
1. Catálogo público: reemplazar `<span>` y `<div class="d-flex flex-wrap gap-2">` por líneas `mb-2` + precio destacado `display-6`
2. Mis Servicios: reemplazar `<div class="d-flex flex-wrap gap-2">` por líneas `mb-2` + precio destacado
3. Tests: actualizar aserciones de layout

**Fuera:** `service_detail.html`, `qr.html`, backend, models, views, archive.

## Capacidades

### Nuevas
Ninguna.

### Modificadas
- `home-public-services-layout`: categoría y período en líneas independientes (`mb-2`, icono `me-1`); precio destacado `display-6 fw-bold text-primary`
- `customer-services-dashboard`: metadata en líneas independientes; período línea propia; precio destacado `display-6 fw-bold text-primary` (solo `commercial`)

## Enfoque

**Patrón detalle a replicar (L25-32):**
```html
<div class="mb-2"><i class="icon me-1 ti ti-tag"></i> Categoría: <strong>{{ display }}</strong></div>
<div class="mb-2"><i class="icon me-1 ti ti-calendar-event"></i> Período: <strong>{{ billing }}</strong></div>
```

**`commercial_public.html` L30-41:** `<span class="d-flex flex-wrap gap-2">` (categoría) + `<div class="d-flex flex-wrap gap-2">` (precio). Reemplazar por líneas `mb-2` independientes.

**`commercial.html` L31-45:** `<div class="d-flex flex-wrap gap-2">` (fechas + pago + precio). Reemplazar por 4-5 `<div class="mb-2">` independientes.

**Decisiones:**
- Período Mis Servicios: línea propia (patrón detalle); precio SOLO monto → sin duplicación
- Período catálogo: omitido (no tiene `start_date/end_date`); precio incluye `<small class="text-secondary">CUP/periodo</small>`
- Iconos categoría: conservar diferenciales (`ti-cloud`/`ti-plant`); patrón detalle usa `ti-tag` genérico

## Áreas afectadas

| Área | Impacto |
|---|---|
| `apps/home/templates/pages/home/services/commercial_public.html` | Modificado — L30-41 |
| `apps/home/templates/pages/home/services/commercial.html` | Modificado — L31-45 |
| `apps/home/tests/test_services_ui.py` | Modificado — aserciones de layout |

## Riesgos

| Riesgo | Prob. | Mitigación |
|---|---|---|
| Tests rompen por cambio DOM | Alta | Actualizar: `test_metadata_layout_order_*`, `test_calendar_icon_precedes_*`, `test_catalog_category_badge_has_*` |
| Precio `display-6` rompe responsive | Baja | Tabler display-6 es responsive; verificar en apply |
| Período duplicado en Mis Servicios | Media | Decisión: período línea propia, precio SOLO monto |

## Plan de reversión

Revert de commits. Sin migraciones (solo templates y tests).

## Dependencias

- `pulido-ui-servicios` (archivado): este cambio refina su layout de metadata.

## Criterios de aceptación

- [ ] Catálogo: categoría y período en líneas `mb-2` independientes con icono `me-1`
- [ ] Catálogo: precio destacado `display-6 fw-bold text-primary`
- [ ] Mis Servicios: fechas, pago, categoría, período, precio — cada uno en línea `mb-2`
- [ ] Mis Servicios: precio destacado `display-6 fw-bold text-primary` (solo `commercial`)
- [ ] Sin duplicación de período
- [ ] Tests actualizados y verdes
- [ ] `manage.py check`, `djlint` OK
