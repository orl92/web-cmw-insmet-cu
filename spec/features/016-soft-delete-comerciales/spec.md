# 016 · Soft delete para modelos comerciales

**Estado:** planificado

## Qué hace

Agrega soft delete (borrado lógico) a los modelos comerciales que actualmente tienen borrado duro: Customer, Service, Invoice, Contract, Certificate. Solo `ServiceSubscription` tiene soft delete actualmente.

## Criterios de aceptación

- [ ] `SoftDeleteModel` abstracto creado en `common/utils.py` con campos `record_active`, `deleted_at`
- [ ] Customer hereda `SoftDeleteModel`
- [ ] Service hereda `SoftDeleteModel`
- [ ] Invoice hereda `SoftDeleteModel`
- [ ] Contract hereda `SoftDeleteModel`
- [ ] Certificate hereda `SoftDeleteModel`
- [ ] Vistas existentes filtran `record_active=True`
- [ ] Sidebar/context_processors filtran soft-deleted
- [ ] `HardDeleteView` para cada modelo (solo superuser)
- [ ] `python manage.py test` — todos pasan
