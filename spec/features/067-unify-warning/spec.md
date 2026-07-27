# Feature 067 · Unify Warning model

## Motivation
Actualmente hay 3 modelos de aviso: `EarlyWarning`, `TropicalCyclone`, `StormWarning` — cada uno con su propia tabla, forms, vistas y templates. Comparten ~80% de la estructura (título, descripción, fecha, activo). Esto triplica el código de CRUD, tests y templates.

## Solución
Fusionar en un solo modelo `Warning` con campo `warning_type`:

```python
WARNING_TYPES = [
    ('early', 'Alerta Temprana'),
    ('cyclone', 'Ciclón Tropical'),
    ('storm', 'Tormenta'),
]
```

### Modelo Warning
- `uuid`, `warning_type`, `title`, `description`, `is_active`, `created_at`, `updated_at`
- Campos específicos de ciclón: `cyclone_name` (nullable), `category` (nullable)
- `record_active` para soft delete (sensible)
- FileHandlerMixin + 4 permisos custom

### Vistas parametrizadas
Una sola vista CRUD por operación, filtrada por `warning_type` en URL:
- `WarningListView` — lista por tipo
- `WarningCreateView` — formulario con fieldset condicional
- `WarningDetailView` — detalle
- `WarningUpdateView` — edición
- `WarningDeleteView` — soft delete

### Templates
- `meteo/warning_list.html` — DataTable unificada
- `meteo/warning_form.html` — form con campos condicionales JS
- `meteo/warning_detail.html` — detalle
- PDF template unificado

## Criterios de aceptación
- `Warning` reemplaza a los 3 modelos anteriores
- Data migration de datos existentes
- Tests de CRUD para cada tipo de warning
- API endpoint unificado con filtro por tipo
- Menú lateral con 3 entradas (una por tipo)
