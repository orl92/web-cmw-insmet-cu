# 069 — tests-comerciales

## Motivación

`apps/commercial/` tiene 7 modelos, 10 forms, 33 vistas y 2 tareas Huey — y cero tests. Es la app con mayor riesgo de regresión y la que maneja datos financieros (facturas, suscripciones pagadas, certificados). Cualquier bug aquí tiene impacto directo en clientes y facturación.

## Cobertura planeada

| Archivo | Sujeto | Tests estimados |
|---|---|---|
| `test_models.py` | 7 modelos: creación, str, UUID, permisos, soft delete, FileHandlerMixin, clean(), save(), unique constraints | ~35 |
| `test_forms.py` | 10 forms: validación, save(), conditional required, regex | ~30 |
| `test_views.py` | 33 vistas: acceso, CRUD, permisos, flujos críticos (aprobar suscripción, cancelar factura, regenerar) | ~45 |
| `test_tasks.py` | 2 tareas Huey: generación PDF + email | ~5 |

Total estimado: ~115 tests.

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
