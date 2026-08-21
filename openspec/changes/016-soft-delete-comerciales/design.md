# 016 · Soft delete para modelos comerciales — Plan

## Enfoque

Crear mixin abstracto reutilizable. NO tocar InvoiceItem (depende de CASCADE de Invoice). Migración agrega campos. Vistas actualizan filtros.

## Implementación

1. Crear `SoftDeleteModel(FileHandlerMixin, models.Model)` en common/utils.py con `record_active`, `deleted_at`, `delete()` (soft), `hard_delete()`, y `SoftDeleteManager`
2. Aplicar a Customer, Service, Invoice, Contract, Certificate
3. Migraciones para cada modelo
4. Actualizar vistas: filtrar `record_active=True`
5. HardDeleteView (solo superuser POST)
6. Actualizar context_processors y sidebar
