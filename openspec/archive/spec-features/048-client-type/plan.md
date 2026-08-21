# Plan — 048 Client Type

## Enfoque técnico

### 1. Modelo (`dashboard/models.py`)

Agregar campo `client_type` a `Customer`:

```python
class ClientType(models.TextChoices):
    NATURAL = 'natural', 'Persona Natural'
    JURIDICA = 'juridica', 'Persona Jurídica'

client_type = models.CharField(
    max_length=10,
    choices=ClientType.choices,
    default=ClientType.JURIDICA,
    verbose_name='Tipo de Cliente'
)
```

Volver opcionales:
- `company_name` → `null=True, blank=True`
- `reeup` → `null=True, blank=True` (quitar `unique` o usar `unique` condicional)
- `nit` → `null=True, blank=True` (quitar `unique` o usar `unique` condicional)

`__str__`: si `company_name` existe, úsalo; si no, usa `user.get_full_name()` o `user.username`.

### 2. Formularios

**`CustomerSignUpForm`** (`accounts/forms/user/form.py`):
- Agregar campo `client_type` (ChoiceField, widget=RadioSelect)
- Eliminar required de `company_name`, `reeup`, `nit` condicionalmente
- `clean()`: si `client_type=natural`, limpiar campos `company_name`, `reeup`, `nit` en `cleaned_data`
- Si `client_type=juridica`, validar como antes
- `save()`: manejar `client_type`, asignar `company_name=None` para natural

**`CustomerForm`, `CustomerUpdateForm`, `CustomerForUserForm`** (`dashboard/forms/clientes/forms.py`):
- Agregar campo `client_type`
- Misma validación condicional

### 3. Templates

**`customer_register.html`**:
- Antes del paso 3, agregar radio `client_type` con opciones "Persona Natural" / "Persona Jurídica"
- JS para mostrar/ocultar bloque de empresa según selección
- Labels condicionales

### 4. Dashboard templates de cliente
- Revisar `templates/pages/dashboard/clientes/` para soportar la visualización de ambos tipos

### 5. Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Tests

- Tests para registro de persona natural (sin REEUP/NIT)
- Tests para registro de persona jurídica (con REEUP/NIT)
- Tests de validación condicional
