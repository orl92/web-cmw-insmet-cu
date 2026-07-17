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
- [x] Templates actualizados con modal dual soft/hard delete
- [x] `python manage.py test` — todos pasan (55 tests)
