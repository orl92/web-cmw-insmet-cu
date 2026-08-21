## Criterios de aceptación

- [ ] `SoftDeleteManager` existe; `Model.objects.all()` no devuelve soft-deleted; `all_objects` sí.
- [ ] Listados comerciales, exports CSV, admin y API pública no muestran borrados.
- [ ] Soft delete NO borra archivos físicos; hard delete SÍ.
- [ ] `Warning` tiene `record_active` y su delete es soft.
- [ ] `generate_invoice_number` no duplica bajo concurrencia (test con dos threads o transacciones).
- [ ] `SiteConfiguration` singleton: no pueden existir 2 filas.
- [ ] `python manage.py check` y `python manage.py test` pasan (ajustar tests que asumían borrados visibles).
