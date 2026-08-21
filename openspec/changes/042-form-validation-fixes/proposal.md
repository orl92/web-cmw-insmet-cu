# 042 — Form validation fixes (Customer uniqueness, Invoice exposure)

## Qué hace
Corrige issues de validación en formularios del dashboard:

1. **CustomerUpdateForm.clean_reeup()** y **CustomerUpdateForm.clean_nit()** no verifican unicidad (el create form sí lo hace)
2. **CustomerForm.clean_account()** no verifica unicidad del campo `account`
3. **InvoiceForm** expone `Customer.objects.all()` sin filtrar por `record_active=True`
4. **InvoiceItemForm** permite seleccionar servicios soft-deleteados (no filtra `record_active=True`)

## Criterios de aceptación
- CustomerUpdateForm rechaza REEUP/NIT duplicados (excluyendo el propio registro)
- CustomerForm rechaza account duplicado
- InvoiceForm solo muestra clientes activos
- InvoiceItemForm solo muestra servicios activos
- Tests pasan
