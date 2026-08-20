- [x] Crear `SoftDeleteModel(models.Model)` abstracto en common/utils.py
- [x] Aplicar a Customer (heredar SoftDeleteModel, migración)
- [x] Aplicar a Service (heredar SoftDeleteModel, migración)
- [x] Aplicar a Invoice (heredar SoftDeleteModel, migración)
- [x] Aplicar a Contract (heredar SoftDeleteModel, migración)
- [x] Aplicar a Certificate (heredar SoftDeleteModel + uuid, migración)
- [x] Refactorizar ServiceSubscription para heredar SoftDeleteModel (eliminar campos/métodos duplicados)
- [x] Actualizar vistas Customer (soft delete en vez de hard delete + CustomerHardDeleteView)
- [x] Actualizar vistas Service (soft delete en vez de hard delete + ServiceHardDeleteView)
- [x] Actualizar InvoiceHardDeleteView para usar hard_delete()
- [x] ContractHardDeleteView
- [x] CertificateHardDeleteView
- [x] Actualizar URLs con rutas de hard delete
- [x] Actualizar templates (clientes, servicios) con modal dual soft/hard delete
- [x] `python manage.py check && python manage.py test` — 55 tests OK

## Fase 2 — Gaps de la auditoría (ver 090-soft-delete-integridad)

- [ ] Crear `SoftDeleteManager` (filtra `record_active=True`) y `all_objects` en `SoftDeleteModel`
- [ ] Auditar `.objects` en listados/exports/admin/API; pasar a `all_objects` solo donde aplique
- [ ] `delete()` (soft) NO borra archivos; `hard_delete()` SÍ
- [ ] `generate_invoice_number` con `select_for_update()`
- [ ] `SiteConfiguration`/`CompanySettings` singleton
- [ ] `python manage.py test` completo tras los cambios de manager
