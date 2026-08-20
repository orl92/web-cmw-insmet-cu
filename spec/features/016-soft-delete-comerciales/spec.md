# 016 · Soft delete para modelos comerciales

**Estado:** completado

## Qué hace

Agrega soft delete (borrado lógico) a los modelos comerciales que actualmente tienen borrado duro: Customer, Service, Invoice, Contract, Certificate. Solo `ServiceSubscription` tiene soft delete actualmente.

## Criterios de aceptación

- [x] `SoftDeleteModel` abstracto creado en `common/utils.py` con campos `record_active`, `deleted_at`
- [x] Customer hereda `SoftDeleteModel`
- [x] Service hereda `SoftDeleteModel`
- [x] Invoice hereda `SoftDeleteModel`
- [x] Contract hereda `SoftDeleteModel`
- [x] Certificate hereda `SoftDeleteModel`
- [x] ServiceSubscription refactorizado para heredar `SoftDeleteModel`
- [x] Vistas existentes filtran `record_active=True`
- [x] Sidebar/context_processors filtran soft-deleted
- [x] `HardDeleteView` para cada modelo (solo superuser)

## Fase 2 — Gaps de la auditoría (090-soft-delete-integridad)

La feature base se completó, pero la auditoría encontró que el soft delete **no funciona realmente**: `SoftDeleteModel` no define manager, `delete()` borra archivos físicos en vez de `hard_delete()`, y la API expone borrados. Los tasks de esta fase viven en la feature 090.

- [ ] `SoftDeleteManager` que filtre `record_active=True` (tasks en 090)
- [ ] `delete()` (soft) conserva archivos; `hard_delete()` los limpia (tasks en 090)
- [ ] Listados/exports/admin/API no muestran borrados (tasks en 090)
- [ ] Race conditions: `generate_invoice_number`, `SiteConfiguration` singleton (tasks en 090)
- [x] Templates actualizados con modal dual soft/hard delete
- [x] `python manage.py test` — todos pasan (55 tests)
