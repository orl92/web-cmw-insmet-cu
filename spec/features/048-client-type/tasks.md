# Tasks — 048 Client Type

## 1. Modelo (`dashboard/models.py`)

- [ ] Agregar `ClientType` TextChoices
- [ ] Agregar campo `client_type` a `Customer`
- [ ] Hacer `company_name` nullable
- [ ] Hacer `reeup` nullable (quitar unique)
- [ ] Hacer `nit` nullable (quitar unique)
- [ ] Actualizar `__str__` para soportar persona natural
- [ ] Actualizar `Meta.verbose_name` si aplica

## 2. Formulario público (`accounts/forms/user/form.py`)

- [ ] Agregar campo `client_type` (RadioSelect)
- [ ] Hacer `company_name` no-required condicionalmente
- [ ] Hacer `reeup` no-required condicionalmente
- [ ] Hacer `nit` no-required condicionalmente
- [ ] `clean()`: validación condicional según `client_type`
- [ ] `save()`: manejar valores None para natural

## 3. Formularios dashboard (`dashboard/forms/clientes/forms.py`)

- [ ] `CustomerForm`: agregar `client_type`, validación condicional
- [ ] `CustomerUpdateForm`: ídem
- [ ] `CustomerForUserForm`: ídem

## 4. Vista de registro (`accounts/views/user/views.py`)

- [ ] Actualizar mensaje de éxito para persona natural (no usa `company_name`)
- [ ] Actualizar `get_context_data` si es necesario

## 5. Template de registro (`customer_register.html`)

- [ ] Agregar radio `client_type` antes del bloque de empresa
- [ ] JS para toggle empresa/persona
- [ ] Labels y placeholders adaptados

## 6. Dashboard templates de cliente

- [ ] Revisar listado/detalle/actualizar para soportar persona natural
- [ ] Mostrar datos correctos según tipo

## 7. Migraciones

- [ ] `python manage.py makemigrations`
- [ ] `python manage.py migrate`

## 8. Verificación

- [ ] `python manage.py check` sin errores
- [ ] `python manage.py test dashboard accounts` — tests existentes OK
- [ ] Prueba manual: registrar persona natural y jurídica
