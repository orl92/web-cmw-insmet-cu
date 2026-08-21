# Spec — 069-tests-comerciales

## Criterios de Aceptación

1. Cada modelo tiene test de creación, `__str__`, UUID, permisos (`default_permissions = ()` + 4 custom).
2. Soft delete: `delete()` → `record_active=False`, `hard_delete()` → físico. En Invoice, Service, Certificate, Customer, Contract, ServiceSubscription.
3. `InvoiceItem.save()` computa `importe = cantidad * precio` y llama `full_clean()`.
4. `ServiceSubscription.clean()` rechaza `start_date >= end_date`.
5. `CustomerForm.save()` crea User + Customer en transacción.
6. `ServiceForm.clean()` valida condicional PUBLIC vs COMMERCIAL.
7. Cada vista ListView requiere login + permiso y retorna 200.
8. `CustomerUpdateView.test_func()` permite solo superuser o propietario.
9. `ApproveSubscriptionView` completa el flujo de pago (certificado + email).
10. `python manage.py test apps.commercial` pasa completo.
11. `python manage.py test` (full suite) no introduce regresiones.
