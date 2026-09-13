# Diseño: Mis Servicios del cliente y limpieza del catálogo comercial

## Objetivo

Reformular "Mis Servicios" para mostrar TODAS las suscripciones (no solo `paid` activas), añadir acciones contextuales por estado, unificar el helper de precio, limpiar el catálogo público de lógica de estado que no le corresponde, y corregir el bug de `client_pending_actions` en el context processor.

## Decisiones de diseño

### 1. Helper único de precio

| Alternativa | Tradeoff | Decisión |
|---|---|---|
| Corregir `get_price_per_period_display()` en el modelo | Simple pero acopla formato de presentación al modelo; rompe API existente en `ServiceDetailView` | **Descartada** |
| Filtro template `format_cup` en `utils_filters.py` | Segregación de responsabilidades; reutilizable en 3 templates sin tocar el modelo; sigue patrón existente (`get_item`, `sanitize_html` ya viven ahí) | **Elegida** |

**Filtro:** `format_cup` en `apps/core/templatetags/utils_filters.py`. Firma: recibe un `Decimal` o `float` y retorna `str`. Formato: separador de miles con punto, decimales con coma (`$1.234,56`). Registra como `@register.filter(name='format_cup')`. Se compone con el período en el template: `{{ service.price|format_cup }} CUP/{{ service.get_billing_period_display }}`. El método `get_price_per_period_display()` del modelo queda sin cambios (se mantiene para compatibilidad interna, no se usa en templates).

### 2. Queryset de CommercialServicesListView

| Opción | Tradeoff | Decisión |
|---|---|---|
| Todos los estados, orden `requested/pending` → `paid` → `expired` | Muestra lo que requiere atención primero; expirados al fondo | **Elegida** |
| Solo `paid` + `requested` + `pending` | Pierde contexto de servicios expirados que el cliente puede renovar | Descartada |
| Todos, orden cronológico | No prioriza acción; usuario debe escanear | Descartada |

**Queryset:** `ServiceSubscription.objects.filter(customer=customer)`. **Orden:** `Case(When(payment_status='requested', then=0), When(payment_status='pending', then=1), When(payment_status='paid', then=2), default=3)`, luego `-start_date` (más reciente primero dentro de cada grupo).

### 3. Ribbon dinámico y acciones contextuales

Se construye un `SUBSCRIPTION_STATUS_MAP` en la vista como `dict` de Python, inyectado al contexto:

```python
STATUS_RIBBONS = {
    'activo': 'bg-green',
    'pendiente de pago': 'bg-orange',
    'solicitado': 'bg-blue',
    'expirado': 'bg-red',
}
```

En `get_context_data`, se añade `context['status_ribbon'] = STATUS_RIBBONS`. El template accede: `status_ribbon|get_item:subscription.status_display`. Reutiliza el filtro `get_item` existente en `utils_filters.py`. No se duplica lógica en el template.

### 4. Acciones por estado (tabla)

| Estado | Acciones (botones) |
|---|---|
| `activo` | Ver PDF certificado (modal, `ti ti-file-type-pdf`) |
| `pendiente de pago` + QR | Ver factura (`ti ti-receipt`, `commercial:factura_list`) + Pagar con QR (`ti ti-qrcode`, `home:payment`) |
| `pendiente de pago` + transfer/presencial | Ver factura (`ti ti-receipt`, `commercial:factura_list`) |
| `solicitado` | Badge "En proceso" sin botones |
| `expirado` | Solicitar (`ti ti-send`, `home:services_commercial_detail`) |

Esto se implementa como un bloque `{% if %}` en el template, consultando `subscription.payment_status` y `subscription.payment_method`. El contexto ya trae `subscription.certificates.first` para el PDF. No se necesita helper adicional en la view para esto — la lógica es puramente de presentación y se resuelve con条件 en el template.

### 5. Catálogo público limpio

**Se elimina de `PublicCommercialServicesListView.get_context_data`:** `user_subscriptions` y `now`.

**Se conserva:** `object_list` (ya viene del `ListView`), `title`, `parent`, `segment`.

**Card resultante:** imagen 200px, título, badge de categoría (`{{ service.get_service_category_display }}`), precio con `format_cup`, summary truncado, código discreto (si existe), botón único: "Solicitar" (logueado) / "Iniciar sesión" (`ti ti-login`, anónimo). Sin ribbons, sin acciones por estado.

### 6. Contador y menú

**Bug fix en `context_processors.py`:** `client_pending_actions = client_requested_count + client_pending_count` se calcula en el path normal (línea ~75), NO solo en el `except`. Actualmente solo se setea en el `except` (línea 82).

**Menú `menu-list.html`:** El item "Mis Servicios" se muestra cuando `client_active_count > 0 OR client_expired_count > 0 OR client_requested_count > 0 OR client_pending_count > 0`. Se reemplaza la condición actual (`client_active_count > 0`) con una más inclusiva. El badge de "Mis Servicios" muestra `client_pending_actions` (requested + pending).

## Cambios por archivo

| Archivo | Acción | Cambio concreto |
|---|---|---|
| `apps/core/templatetags/utils_filters.py` | Modificar | Añadir filtro `format_cup` (formato locale `es-mx` con separador de miles) |
| `apps/home/views/servicios/comerciales/views.py` | Modificar | `CommercialServicesListView`: queryset sin filtro de estado + orden Case/When; `PublicCommercialServicesListView`: eliminar `user_subscriptions`/`now` del contexto |
| `apps/core/context_processors.py` | Modificar | Calcular `client_pending_actions` en el path normal del bloque client |
| `templates/includes/home/menu-list.html` | Modificar | Condición Mis Servicios: ≥1 suscripción (cualquier estado); badge con `client_pending_actions` |
| `apps/home/templates/pages/home/services/commercial.html` | Modificar | Ribbon dinámico, acciones contextuales por estado, precio con `format_cup`, calendario antes del rango, método de pago |
| `apps/home/templates/pages/home/services/commercial_public.html` | Modificar | Eliminar bloques de ribbon/botones por estado; añadir badge categoría, precio `format_cup`, código discreto, botón único con iconos |
| `apps/home/templates/pages/home/services/service_detail.html` | Modificar | Submit "Solicitar" + `ti ti-send`, Cancelar `ti ti-x`, precio con `format_cup` |
| `apps/home/tests/test_services_ui.py` | Modificar | Tests de ribbon dinámico, acciones por estado, precio format, limpieza catálogo |
| `apps/commercial/tests/test_views.py` | Modificar | Aserciones de precio actualizadas al nuevo formato `format_cup` |

## Lógica de negocio

### Estados y transiciones (sin cambios de modelo)

`requested` → `pending` (staff factura) → `paid` (cliente paga) → `expired` (fecha fin). Re-solicitud crea fila `requested` junto a la vigente. El botón "Solicitar" en catálogo y detail siempre redirige al `ServiceDetailView`; el `form_valid` decide si bloquea (in-flight exists) o crea.

### Contador `client_pending_actions`

```
client_pending_actions = client_requested_count + client_pending_count
```

Se calcula DESPUÉS de ambos queries en el path normal (no solo en el `except`).

### Visibilidad "Mis Servicios" en menú

```
mostrar_mis_servicios = client_active_count + client_expired_count + client_requested_count + client_pending_count > 0
```

## UI/UX

### Card "Mis Servicios" (Tabler)

```
col-sm-6 col-lg-4
┌─────────────────────────┐
│  [imagen 200px cover]   │
│  ┌──────────────┐       │
│  │ ribbon bg-*  │       │  ← dinámico por status_display
│  └──────────────┘       │
├─────────────────────────┤
│ Título (link → detail)  │
│ Summary truncado 200ch  │
│                         │
│ 📅 dd/mm/yyyy - dd/mm/yyyy │  ← calendario ANTES
│ 💳 Método de pago           │
│ 💲 $1.234,56 CUP/mes        │  ← helper format_cup
│                         │
│ [acciones por estado]   │
└─────────────────────────┘
```

### Card catálogo público

```
col-sm-6 col-lg-4
┌─────────────────────────┐
│  [imagen 200px cover]   │
├─────────────────────────┤
│ Título (link → detail)  │
│ Badge: Agrometeorológico│  ← service_category_display
│ Summary truncado 200ch  │
│ 💲 $1.234,56 CUP/mes        │
│ Código: C200 (discreto) │  ← solo si existe
│                         │
│ [Solicitar / Iniciar sesión]  ← botón único, sin ribbons
└─────────────────────────┘
```

### Iconos (mismos que proposal)

- Pagar QR: `ti ti-qrcode`
- Iniciar sesión: `ti ti-login`
- Ver (relacionados): `ti ti-eye`
- Submit detail: `ti ti-send`
- Cancelar: `ti ti-x`
- Ver factura: `ti ti-receipt`
- Ver PDF certificado: `ti ti-file-type-pdf`

### Colores ribbon

| status_display | Clase Tabler |
|---|---|
| activo | `bg-green` |
| pendiente de pago | `bg-orange` |
| solicitado | `bg-blue` |
| expirado | `bg-red` |

## Tests

| Qué | Dónde | Approach |
|---|---|---|
| `format_cup` filtro | `apps/core/tests/test_templatetags.py` (nuevo o existente) | Unit: decimales, enteros, None, separador miles |
| CommercialServicesListView muestra todos los estados | `apps/home/tests/test_services_ui.py` | Integration: crear subs requested/pending/paid/expired, verificar que todas aparecen |
| Ribbon dinámico por estado | `apps/home/tests/test_services_ui.py` | Integration: verificar clase CSS correcta por estado |
| Acciones contextuales | `apps/home/tests/test_services_ui.py` | Integration: verificar botones/URLs por estado |
| Catálogo público sin ribbons | `apps/home/tests/test_services_ui.py` | Integration: verificar que NO aparecen ribbons/botones de estado |
| Catálogo con precio format_cup | `apps/home/tests/test_services_ui.py` | Integration: verificar formato `$1.234,56 CUP` en HTML |
| `client_pending_actions` en path normal | `apps/core/tests/test_context_processors.py` (o existente) | Unit: simular request con subs requested+pending, verificar variable |
| Menú badge "Mis Servicios" visible con ≥1 sub | `apps/home/tests/test_services_ui.py` | Integration: verificar visibilidad con distintos estados |
| Detail submit "Solicitar" | `apps/home/tests/test_services_ui.py` | Integration: verificar texto y icono `ti ti-send` |

**Tests afectados (aserciones a actualizar):**
- `ServiceReRequestUiTests.test_active_paid_renders_form_and_cta` — actualmente aserta `Solicitar de nuevo`; se cambia a `Solicitar`
- `ServiceReRequestUiTests.test_public_list_active_shows_re_request_button` — aserta `Solicitar de nuevo`; se cambia a `Solicitar` y se eliminan assertions de ribbon en catálogo
- `ServiceReRequestUiTests.test_public_list_requested_shows_no_button` — aserta ribbon `Solicitado` en catálogo; se elimina
- `ServiceReRequestUiTests.test_public_list_deterministic_precedence` — aserta ribbon en catálogo; se elimina
- `ServicesCommercialStaffButtonTests.test_pending_non_qr_shows_invoice_guidance` — se verifica que sigue funcionando
- Tests de precio en `test_views.py` (`$45.50`) → actualizar a formato `format_cup`

## Riesgos y mitigaciones

| Riesgo | Prob. | Mitigación |
|---|---|---|
| Tests existentes rompen por cambio de formato precio | Alta | Buscar todas las aserciones de formato en tests y actualizarlas en un solo paso |
| `ServiceReRequestUiTests` asertan ribbons/botones del catálogo que se eliminan | Alta | Revisar cada test del archivo; los que asertan `Solicitado`/`Activo`/`Solicitar de nuevo` en el catálogo se actualizan o eliminan según el nuevo diseño |
| Locale `es-mx` no disponible en entorno de test | Baja | `format_cup` implementa el formateo manualmente (no depende de `locale.setlocale`) |
| Queryset sin filtro de estado carga más registros | Baja | `paginate_by=10` ya limita; `select_related` mantiene eficiencia |

## Preguntas abiertas

- [ ] Confirmar que el texto del submit del detail debe ser "Solicitar" siempre (no "Solicitar de nuevo" cuando hay active subscription). El proposal dice unificar.
- [ ] El template `commercial_public.html` carga `{% load my_filters %}` — verificar que el filtro `format_cup` queda disponible vía `my_filters.py` (ya importa `utils_filters.py`, así que sí).
