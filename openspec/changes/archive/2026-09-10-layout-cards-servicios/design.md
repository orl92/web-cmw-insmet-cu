# Diseño: Layout Cards Servicios

## Enfoque técnico

Cambio template-only (2 templates + tests, 0 backend) que replica el patrón de metadata de `service_detail.html` L25-32 (`<div class="mb-2">` + icono `me-1` + label + `<strong>`) en los cards del catálogo público y Mis Servicios: cada metadata en línea `mb-2` independiente, precio destacado `display-6 fw-bold text-primary`, categoría del catálogo con icono diferencial (`ti-cloud`/`ti-plant`) y resolución de `ti-calendar` → `ti-calendar-month`.

**Baseline (verificado ejecutando tests):** `test_calendar_icon_precedes_date_range_in_dom` y `test_metadata_layout_order_is_dates_payment_price` están hoy ROJOS — `ti-calendar-month` no existe en ningún template (`commercial.html` L33 renderiza `ti-calendar`). El template corregido deja verde el primero.

## Decisiones de arquitectura

### D1. Pin vertical del card — wrapper `flex-grow-1`

| Opción | Tradeoff | Decisión |
|---|---|---|
| (a) Wrapper `d-flex flex-column flex-grow-1 mb-3` con todas las líneas dentro | Pin en una sola región; metadata pegada al summary; `flex-grow-1` absorbe el espacio libre del `card-body d-flex flex-column`; no toca acciones | **Elegida** |
| (b) Líneas sueltas + `mt-auto` en acciones | Exige editar acciones en ambos templates (`mt-auto` falta en Mis Servicios) | Descartada |
| (c) `mt-auto mb-3` literal en la última línea (precio) | Despega el precio de categoría/período (la "metadata partida" que se elimina) | Descartada |

**Razonamiento:** el DOM actual es inconsistente — el catálogo tiene TRES `mt-auto` (categoría, precio, acciones) que reparten el espacio libre; Mis Servicios apoya todo el pin en su único bloque. (a) unifica el mecanismo, confina el cambio a la metadata y deja las acciones intactas (`mt-auto` del catálogo queda redundante e inofensivo).

**Reconciliación con specs:** ambas exigen que el "último bloque de metadata conserve `mt-auto mb-3`". La intención (acciones al fondo del `h-100`) se cumple con `flex-grow-1` + `mb-3` en el wrapper; ningún escenario aserta `mt-auto`, sin conflicto con tests.

### D2. `display-6` en cards `col-lg-4` — se conserva

| Opción | Tradeoff | Decisión |
|---|---|---|
| `display-6 fw-bold text-primary` en ambos | Fluid en Tabler (≈24-29px según viewport, card ~350px); lo asertan los escenarios de spec | **Elegida** |
| `h3`/`h4` + `fw-bold text-primary` | Rompe los escenarios de spec (implicaría revisar specs; fuera del alcance) | Descartada |

**Mitigación:** QA visual a 360px en apply; si desborda, escalar a revisión de specs — no cambiar la clase en silencio.

### D3. Estructura DOM destino

Wrapper en ambos: `<div class="d-flex flex-column flex-grow-1 mb-3 text-secondary">` con líneas `<div class="mb-2">` dentro; acciones intactas.

**Catálogo** (reemplaza L30-41) — 3 líneas:

| Línea | Icono | Contenido |
|---|---|---|
| Categoría | `ti-cloud`/`ti-plant` | "Categoría:" + `<strong>{{ service.get_service_category_display }}</strong>` |
| Período | `ti-calendar-event` | "Período:" + `<strong>{{ service.get_billing_period_display }}</strong>` |
| Precio | — | `display-6 fw-bold text-primary`: `format_cup|default_if_none:'—'` + `<small class="text-secondary">CUP/{{ service.get_billing_period_display }}</small>` |

**Mis Servicios** (reemplaza L31-45) — 4-5 líneas: Fechas (`ti-calendar-month`, corrige L33), Pago con `payment_method_icon` si `payment_method` existe, Categoría (`ti-tag` + `strong`), Período (`ti-calendar-event` + `strong`), Precio solo monto si `commercial` (sin sufijo, evita duplicar período).

## Flujo de datos

Template-only; el orden DOM es el contrato bajo test: `card-body (d-flex flex-column, h-100)` → título + summary → wrapper `flex-grow-1 mb-3` (líneas `mb-2`) → precio destacado → acciones al fondo.

## Cambios por archivo

| Archivo | Acción | Cambios |
|---|---|---|
| `apps/home/templates/pages/home/services/commercial_public.html` | Modificar | L30-41 → wrapper + 3 líneas; precio `display-6` + `<small>CUP/…</small>` |
| `apps/home/templates/pages/home/services/commercial.html` | Modificar | L31-45 → wrapper + 4-5 líneas; L33 `ti-calendar` → `ti-calendar-month`; precio solo monto |
| `apps/home/tests/test_services_ui.py` | Modificar | Re-escopear metadata order; reforzar iconos catálogo; tests RED nuevos |

## Estrategia de tests

| Test | Acción |
|---|---|
| `test_metadata_layout_order_is_dates_payment_price` | **Actualizar**: marcador región `d-flex flex-wrap gap-2 text-secondary mt-auto mb-3` → `d-flex flex-column flex-grow-1 mb-3`; orden fechas → pago → categoría (`ti-tag`) → período (`ti-calendar-event`) → precio; marcador precio `$` (ya no `CUP/`) |
| `test_calendar_icon_precedes_date_range_in_dom` | **Sin cambio** — corregir el template lo deja verde (hoy rojo) |
| `test_catalog_category_badge_has_cloud_icon` / `_plant_icon` | **Actualizar** (spec): icono `me-1` ANTES de "Categoría:" en su línea `mb-2` |
| Sin cambio | `test_public_list_active_shows_state_neutral_card`, `test_catalog_shows_category_badge_and_code`, `test_catalog_no_currency_dollar_icon`, `test_subscription_payment_icon_*`, `test_subscription_no_dollar_icon_in_price`, `test_pending_*`, `test_requested_*` (aserciones siguen satisfechas) |
| **Nuevos RED** (escenarios sin cobertura) | Catálogo: orden categoría→período→precio; precio `display-6` con `CUP/período`. Mis Servicios: sin `payment_method` omite línea; precio solo `commercial`; líneas con `<strong>`; icono `presencial` (`ti-building-store`) |

Grep previo en `apps/**/*.py` (`flex-wrap`, `gap-2 text-secondary`, `mt-auto mb-3`, `CUP/`, `ti-cloud/plant`): **no existen otros tests** del layout actual.

**Verificación:** `python manage.py test apps.home.tests.test_services_ui` → `python manage.py test apps.home` → `python manage.py check` → `djlint . --reformat --check` + `djlint . --lint`.

## Amenaza y seguridad

N/A — sin routing, shell, subprocess, VCS/PR automation, executable-file classification, ni process-integration boundary.

## Migración / despliegue

Sin migraciones ni datos. Solo templates y tests; deploy estándar; sin feature flags. Reversión: revert.

## Preguntas abiertas

- [ ] Ninguna bloqueante. QA de `display-6` a 360px en apply (D2); si no convence, revisar specs después.