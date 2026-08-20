# 090 · Integridad de datos y soft delete — Plan

## Enfoque

El cambio central es el `SoftDeleteManager` (cambia el comportamiento global de querysets). Los demás frentes son localizados. Orden sugerido: manager → cleanup → Warning → races.

## Implementación

1. **SoftDeleteManager** — en `apps/core/models.py` junto a `SoftDeleteModel`:
   - `class SoftDeleteManager(models.Manager): def get_queryset(self): return super().get_queryset().filter(record_active=True)`
   - `class SoftDeleteModel(...): objects = SoftDeleteManager(); all_objects = models.Manager()`
   - Migración no requerida (no cambia esquema).
   - Verificar impacto: correr suite completa; ajustar tests que creaban registros borrados y esperaban verlos en querysets por defecto.
   - Revisar FKs: si una FK apunta a un modelo soft-delete, el accessor usa el manager por defecto (filtrará borrados) — esperado.

2. **Cleanup** — invertir:
   - `delete()` (soft) → NO `_cleanup_files()`.
   - `hard_delete()` → `_cleanup_files()` antes de `super().hard_delete()`.
   - Verificar `FileHandlerMixin` y tests de `FileHandlingTestCase`.

3. **Warning** — `apps/meteo/models.py:280`:
   - `class Warning(FileHandlerMixin, SoftDeleteModel)`.
   - `WarningDeleteView` → soft delete.
   - Migración para `record_active`/`deleted_at`.

4. **Races**:
   - `generate_invoice_number` → `select_for_update()` dentro de transacción sobre la última factura (o `get_or_create` con unique constraint y retry).
   - `SiteConfiguration.save()` → forzar pk=1 (o check + raise); `get_instance()` → `get_or_create(pk=1)`.

## Riesgos

- **SoftDeleteManager es un cambio global**: cualquier código que hoy depende de ver registros borrados (ej. exports que exportan todo, admin, reportes históricos) cambiará de comportamiento. Hay que auditar cada uso de `.objects` sobre modelos soft-delete antes de aplicar, y decidir cuáles pasan a `all_objects` (ej. exports históricos legítimos, admin).
- Tests existentes que crean borrados y los esperan en querysets por defecto romperán → ajustar a `all_objects` donde sea legítimo.
- `select_for_update` en SQLite no bloquea realmente (SQLite no soporta row locks) → en dev no se verá el efecto; funciona en PostgreSQL/MySQL (prod). Documentar.

## Verificación

- `python manage.py check`
- `python manage.py test` (completa; ajustar tests afectados)
- Test manual: soft delete un Customer → no aparece en listado ni API; archivo PDF sigue en disco; `all_objects` lo muestra.
- Test manual: hard delete → archivo eliminado.
- `python manage.py makemigrations` (Warning + posibles cambios) y `migrate`.
