# Design: Servicios Comerciales por Tipo (Categoría de Facturación)

## Decisiones de Arquitectura

| Decisión | Alternativas | Tradeoff | Decisión |
|----------|-------------|----------|----------|
| Campo `service_category` en `Service` | Opción A (`billing_period` por servicio), Opción B (categoría que deriva período) | Opción A más flexible; Opción B más simple, alineada al modelo de negocio real | **Opción B** — `agrometeo` (mensual) / `pronostico` (diario), default `pronostico` |
| Cálculo de `end_date` mensual | `dateutil.relativedelta` (ya en requirements), cálculo manual con `calendar.monthrange` | `dateutil` ya es dependencia; handling manual de fin de mes es propenso a bugs | **`dateutil.relativedelta`** para agrometeo; `timedelta(days=quantity)` para pronóstico |
| Ubicación del helper `compute_end_date` | Método estático en `ServiceSubscription`, función utilitaria separada | Helpers en el modelo son más cohesivos con la lógica de negocio | **Método estático en `Service`** — `Service.compute_end_date(start_date, quantity)` |
| `PERIOD_DAYS` | Eliminar, deprecar, mantener como alias | Eliminar rompe tests existentes; mantenerlo como alias preserva compatibilidad | **Mantener como alias** `PERIOD_DAYS = 1` (default diario), agregar `PERIOD_MONTHS = 1`; método `get_billing_period_display()` |
| Campo `quantity` | En `ServiceSubscription` como IntegerField, default 1 | Default 1 preserva suscripciones existentes sin data migration adicional | **IntegerField, default=1, validators=[MinValueValidator(1)]** |

## Adiciones de Modelos

### `Service` — campos y métodos nuevos

```python
# Campo nuevo (línea ~118, después de price)
service_category = models.CharField(
    max_length=10,
    choices=[('agrometeo', 'Agrometeorológico'), ('pronostico', 'Pronóstico')],
    default='pronostico',
    verbose_name='Categoría del servicio',
)
```

**Métodos nuevos:**
- `get_billing_period_display()` → `"mes"` o `"día"` según categoría
- `get_price_per_period_display()` → `"$120.00 / mes"` o `"$10.00 / día"`
- `compute_end_date(start_date, quantity)` (estático): usa `relativedelta(months=quantity)` para agrometeo, `timedelta(days=quantity)` para pronóstico

**`PERIOD_DAYS`:** Se mantiene como constante `= 1` (antes era 30). Se agrega `PERIOD_MONTHS = 1`. El antiguo valor 30 se elimina de forma que todo el código usa `quantity × período`.

### `ServiceSubscription` — campo nuevo

```python
quantity = models.PositiveIntegerField(
    default=1,
    validators=[MinValueValidator(1)],
    verbose_name='Cantidad',
    help_text='Meses (agrometeo) o días (pronóstico)',
)
```

## Cambios de Modelos

### `Service.PERIOD_DAYS` (línea 94)

- **Antes:** `PERIOD_DAYS = 30`
- **Ahora:** `PERIOD_DAYS = 1` (alias para consistencia con pronóstico)
- Se agrega `PERIOD_MONTHS = 1`

### `ServiceSubscription.clean()` (línea 189)

Agregar validación: si `start_date` y `end_date` existen y `start_date >= end_date`, levantar `ValidationError`.

## Endpoints / Formas

### Fix permiso `ajax_pending_subscriptions` (invoices.py:445)

```python
# Antes:
@permission_required('commercial.view_servicesubscription')
# Ahora:
@permission_required('commercial.view_subscription')
```

### `ajax_pending_subscriptions` — retornar `quantity` en data attributes

Agregar `data-quantity="{sub.quantity}"` al checkbox HTML, para que el JS del frontend pueda usarlo en lugar de calcular días.

### `process_batch_invoice` (invoices.py:146)

```python
# Antes (línea 149):
days_count = (end_date - start_date).days
amount = price * days_count
cantidad=days_count,

# Ahora:
quantity = sub.quantity
amount = sub.service.price * quantity
cantidad=quantity,
unidad_medida='MES' if sub.service.service_category == 'agrometeo' else 'DÍA',
```

### `process_manual_invoice` (invoices.py:214)

```python
# Antes (línea 222):
days_count = (end_date - start_date).days
cantidad=days_count,
importe=days_count * cd['precio'],

# Ahora:
# Determinar quantity del servicio seleccionado
service = cd['service']
quantity = 1  # default para facturación manual
unidad_medida = 'MES' if service.service_category == 'agrometeo' else 'DÍA'
cantidad=quantity,
importe=quantity * cd['precio'],
```

### `SubscriptionRenewView.form_valid` (subscriptions.py:148)

```python
# Antes (línea 154):
end_date=timezone.now() + timedelta(days=30),

# Ahora:
service = old.service
new_quantity = old.quantity
end_date = Service.compute_end_date(timezone.now(), new_quantity, service.service_category)
```

## Vista (Template) / Flujo UI

### `PaymentMethodForm` (forms/subscription.py:105)

Reemplazar `end_date` por `quantity`:

```python
class PaymentMethodForm(forms.Form):
    PAYMENT_METHOD_CHOICES = [...]  # sin cambios
    payment_method = forms.ChoiceField(...)
    start_date = forms.DateField(...)  # sin cambios
    quantity = forms.IntegerField(
        min_value=1,
        label='Cantidad',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
    )
```

El label se condiciona en el template según `service.service_category`:
- `pronostico`: "Cantidad de días"
- `agrometeo`: "Cantidad de meses"

### `ServiceDetailView` (home/views/servicios/comerciales/views.py:75)

```python
# Antes (línea 82):
context['estimated_total'] = price * Service.PERIOD_DAYS if price else 0

# Ahora:
context['estimated_total'] = price * 1 if price else 0  # precio por período
context['billing_period'] = self.service.get_billing_period_display()
```

### `ServiceDetailView.form_valid` (línea 108)

```python
# Antes:
start_date = form.cleaned_data['start_date']
end_date = form.cleaned_data['end_date']

# Ahora:
start_date = form.cleaned_data['start_date']
quantity = form.cleaned_data['quantity']
end_date = Service.compute_end_date(start_date, quantity, self.service.service_category)
```

Crear `ServiceSubscription` con `quantity=quantity, start_date=..., end_date=...`.

### Template `service_detail.html`

Cambiar:
- Línea 27: `Período estándar: <strong>{{ service.PERIOD_DAYS }} días</strong>` → `Período: <strong>{{ service.get_billing_period_display }}</strong>`
- Línea 32: `Precio: ...` → `Precio por {{ service.get_billing_period_display }}: <strong>${{ service.price|floatformat:2 }}</strong>`
- Línea 36: `Monto estimado ({{ service.PERIOD_DAYS }} días)` → `Monto estimado (1 {{ service.get_billing_period_display }}): ...`
- Línea 69-84: Reemplazar campo `end_date` por `quantity` con label condicional
- Agregar JS para label dinámico según categoría del servicio (pasada como `data-category`)

### Template `commercial_public.html` — Bloque staff

Insertar después de la imagen (línea 32) y antes del card-body:

```html
{% if perms.commercial.change_service or perms.commercial.add_service %}
  <div class="d-flex gap-2 mt-2">
    {% if perms.commercial.change_service %}
      <a href="{% url 'commercial:servicio_update' service.uuid %}"
         class="btn btn-outline-warning btn-sm">
        <i class="icon ti ti-edit"></i> Editar
      </a>
    {% endif %}
    {% if perms.commercial.add_service %}
      <a href="{% url 'commercial:servicio_create' %}"
         class="btn btn-outline-success btn-sm">
        <i class="icon ti ti-plus"></i> Nuevo servicio
      </a>
    {% endif %}
  </div>
{% endif %}
```

### Template `commercial_public.html` — Guía pending sin QR

En el bloque de `sub.payment_status == 'pending'` y método no-QR (línea 55-56):

```html
{% elif sub.payment_method != 'qr' %}
  <a href="{% url 'commercial:factura_list' %}"
     class="btn btn-outline-secondary btn-sm">
    <i class="icon ti ti-receipt"></i> Ver factura
  </a>
```

## Consideraciones Técnicas

### Helper `compute_end_date`

```python
@staticmethod
def compute_end_date(start_date, quantity, category='pronostico'):
    if category == 'agrometeo':
        return start_date + relativedelta(months=quantity)
    return start_date + timedelta(days=quantity)
```

Ubicación: método estático en `Service` (models.py, después de `get_image_url`). Importar `from dateutil.relativedelta import relativedelta`.

### Validación

- `quantity ≥ 1`: validado por `MinValueValidator` en el modelo y `min_value=1` en el form
- `end_date > start_date`: validado en `ServiceSubscription.clean()` y en `ServiceDetailView.form_valid`
- No se limita quantity máximo — el cliente elige libremente

### Template JS — Label dinámico de quantity

En `service_detail.html`, pasar `service.service_category` como `data-category` al form. El JS lee el atributo y actualiza el label del campo quantity:
- `pronostico` → "Cantidad de días"
- `agrometeo` → "Cantidad de meses"

## Dependencias

- `python-dateutil` — **ya presente** en `requirements.txt`

## Migración

1. `makemigrations` para `Service` (campo `service_category`, default `'pronostico'`)
2. `makemigrations` para `ServiceSubscription` (campo `quantity`, default `1`)
3. Data migration: `Service.objects.filter(service_type='commercial').update(service_category='pronostico')` (ya cubierto por default)
4. Migraciones NO se versionan en git (`.gitignore`); se corren en cada entorno

## Tests a Actualizar

| Test | Archivo | Cambio necesario |
|------|---------|-----------------|
| `test_period_days_constant` | `test_service_detail.py:15` | Cambiar `assertEqual(Service.PERIOD_DAYS, 30)` → `assertEqual(Service.PERIOD_DAYS, 1)` |
| `test_template_renders_...` | `test_service_detail.py:44-45` | Cambiar assertions de "30 días" a assertions de categoría display |
| `ServicesCommercialUiTests` | `test_services_ui.py` | Agregar tests de staff buttons en `commercial_public.html` |
| Tests de `SubscriptionRenewView` | `test_views.py` (si existen) | Verificar que renovación usa `quantity × período` |
| Tests de `process_batch_invoice` | `test_views.py` (si existen) | Verificar `cantidad=quantity`, no `days_count` |
| Tests de `ajax_pending_subscriptions` | `test_views.py` (si existen) | Verificar permiso `view_subscription` |

## Riesgos

- **PERIOD_DAYS = 1 rompe tests existentes**: mitigado actualizando tests explícitamente
- **Suscripciones existentes con quantity=1**: default preserva comportamiento actual (1 día para pronóstico)
- **Facturas batch existentes**: no se ven afectadas — el cambio es solo para facturas nuevas

## Open Questions

- [ ] ¿El form de staff (`SubscriptionForm`) también debe cambiar a usar quantity en vez de period presets? (Actualmente usa `PERIOD_CHOICES` con timedelta)
- [ ] ¿La unidad_medida en `InvoiceItem` debe cambiar a "MES"/"DÍA" según categoría, o mantener "U"?
