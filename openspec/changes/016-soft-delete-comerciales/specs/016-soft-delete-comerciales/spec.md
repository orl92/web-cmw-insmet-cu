# Spec — 016-soft-delete-comerciales

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
