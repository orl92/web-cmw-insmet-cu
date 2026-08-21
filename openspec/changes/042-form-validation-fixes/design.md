# Plan — 042-form-validation-fixes

## Enfoque técnico
### CustomerUpdateForm (forms/clientes/forms.py)
- `clean_reeup()`: agregar `Customer.objects.filter(reeup=reeup).exclude(pk=self.instance.pk).exists()`
- `clean_nit()`: mismo patrón
- `clean_account()`: agregar validación de unicidad (y considerar agregar `unique=True` al campo del modelo)

### CustomerForm.clean_account()
- Agregar `Customer.objects.filter(account=account).exists()` check

### InvoiceForm (forms/facturacion/forms.py)
- Cambiar queryset a `Customer.objects.filter(record_active=True)`

### InvoiceItemForm (forms/facturacion/forms.py)
- Cambiar queryset a `Service.objects.filter(service_type=Service.COMMERCIAL, record_active=True)`

## App(s) modificadas
- dashboard/forms/clientes/forms.py
- dashboard/forms/facturacion/forms.py
