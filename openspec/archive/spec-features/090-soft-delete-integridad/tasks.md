# Tasks — 090-soft-delete-integridad

## SoftDeleteManager

- [ ] `apps/core/models.py` — Crear `SoftDeleteManager` que filtre `record_active=True` por defecto.
- [ ] `apps/core/models.py` — `SoftDeleteModel.objects = SoftDeleteManager()` y `all_objects = models.Manager()`.
- [ ] Auditar usos de `.objects` sobre modelos soft-delete (Customer, Service, ServiceSubscription, Invoice, Contract, Certificate, Warning):
  - Listados/vistas → dejan el default (ya filtran).
  - Exports CSV que deben incluir históricos → pasar a `all_objects` explícitamente (justificar).
  - Admin → decidir: `all_objects` si debe mostrar borrados, o default.
  - API pública → default (no exponer borrados).
- [ ] Ajustar tests existentes que crean registros borrados y los esperan en querysets por defecto (usar `all_objects` donde sea legítimo).
- [ ] Test: soft delete no aparece en `.objects.all()`, sí en `.all_objects.all()`.

## Cleanup de archivos

- [ ] `apps/core/models.py` — `SoftDeleteModel.delete()` (soft): NO llamar `_cleanup_files()`.
- [ ] `apps/core/models.py` — `hard_delete()`: llamar `_cleanup_files()` antes de borrar la fila.
- [ ] Verificar `FileHandlerMixin._cleanup_files()` (`core/models.py:41-47`) y su uso.
- [ ] Test (`core/tests/base.py` FileHandlingTestCase o similar): soft delete conserva el archivo; hard delete lo elimina.

## Warning soft delete

- [ ] `apps/meteo/models.py:280` — `Warning` hereda `SoftDeleteModel` (con FileHandlerMixin).
- [ ] `apps/meteo/views/warning.py:257` — `WarningDeleteView` → soft delete.
- [ ] `makemigrations` + `migrate` (agrega `record_active`/`deleted_at` a Warning).
- [ ] Verificar listado de warnings no muestre borrados.

## Race conditions

- [ ] `apps/commercial/views/invoices.py:289-298` — `generate_invoice_number` con `select_for_update()` en transacción (o retry con IntegrityError). Documentar limitación SQLite.
- [ ] `apps/core/models.py:147-150` — `SiteConfiguration.save()`: forzar singleton (pk=1 o check + raise).
- [ ] `apps/core/models.py:186-200` — `CompanySettings.get_instance()` → `get_or_create(pk=1)` (o similar).
- [ ] Test: no pueden existir 2 `SiteConfiguration`.

## Verificación

- [ ] `python manage.py check`
- [ ] `python manage.py test`
- [ ] Actualizar roadmap.md (mover 090 a Hecho al completar).
- [ ] Commit.
