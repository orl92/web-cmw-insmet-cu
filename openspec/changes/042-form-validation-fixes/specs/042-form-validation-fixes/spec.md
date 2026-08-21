# Spec — 042-form-validation-fixes

## Criterios de aceptación
- CustomerUpdateForm rechaza REEUP/NIT duplicados (excluyendo el propio registro)
- CustomerForm rechaza account duplicado
- InvoiceForm solo muestra clientes activos
- InvoiceItemForm solo muestra servicios activos
- Tests pasan
