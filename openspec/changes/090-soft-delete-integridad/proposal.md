# 090-soft-delete-integridad · Integridad de datos y soft delete

## Motivación

Auditoría de modelos encontró problemas de integridad sistémicos:

1. **Soft delete roto por diseño** — `SoftDeleteModel` (`apps/core/models.py:53-68`) define `record_active`/`deleted_at` y sobreescribe `delete()`, pero **no define ningún Manager**. `Model.objects.all()` devuelve registros borrados. La convención de AGENTS.md ("usa el manager por defecto, no all_objects") es imposible de cumplir porque ese manager no existe. Afecta: listados (`customers.py:41`, `services.py:33`, `contracts.py:20`), **todos los CSV exports** (`core/views/exports.py:27`), el **admin** (ningún ModelAdmin filtra) y la **API pública** (`api/views.py:187` expone servicios soft-deleted).
2. **Cleanup de archivos invertido** — `SoftDeleteModel.delete()` llama `_cleanup_files()` (`core/models.py:61-62`) que **borra físicamente los PDFs/imágenes** aunque el registro sigue en DB con `record_active=False`; `hard_delete()` (líneas 67-68) llama al delete de Model **sin** cleanup → archivos huérfanos en disco. Debería ser al revés.
3. **`Warning` sin soft delete** — `apps/meteo/models.py:280` (`Warning(FileHandlerMixin, models.Model)`). AGENTS.md lista **Warning** explícitamente entre los modelos que deben usar `SoftDeleteModel`. `WarningDeleteView` (`meteo/views/warning.py:257`) hace borrado físico de avisos históricos.
4. **Race conditions**:
   - `generate_invoice_number` (`apps/commercial/views/invoices.py:289-298`) — lee el último número y calcula `num+1` sin lock ni transacción atómica → dos creaciones concurrentes generan el mismo número y estallan en `IntegrityError` (unique).
   - `SiteConfiguration.save()` (`apps/core/models.py:147-150`) — si ya existe una fila, retorna sin error ni aviso; dos creates concurrentes crean dos filas. Mismo patrón en `CompanySettings.get_instance()` (líneas 186-200).

## Solución

### 1. `SoftDeleteManager`
- Crear `SoftDeleteManager(models.Manager)` que filtre `record_active=True` por defecto.
- Definirlo como `objects` en `SoftDeleteModel`.
- Agregar `all_objects` (manager sin filtro) para administración.
- Actualizar `default_related_name` si aplica (las FKs hacia modelos soft-delete usarán el manager por defecto).
- Los ModelAdmin que deban ver borrados usarán `all_objects` explícitamente; el resto queda con el filtro automático.
- **Ojo**: esto cambia el comportamiento de TODOS los querysets existentes que hoy muestran borrados (ahora correcto) pero también de los que ya filtran manualmente (doble filtro inofensivo).

### 2. Cleanup de archivos
- `SoftDeleteModel.delete()` (soft) → NO llamar `_cleanup_files()` (el registro queda, el archivo debe quedar).
- `hard_delete()` → llamar `_cleanup_files()` antes de borrar la fila.
- Verificar `FileHandlerMixin` (`core/models.py:41-47`) para que el cleanup solo ocurra en hard delete.

### 3. Warning con soft delete
- `Warning` hereda `SoftDeleteModel` en vez de `models.Model`.
- `WarningDeleteView` → soft delete (llamar `delete()` que ahora es soft).
- Si se necesita borrado físico, vista explícita con permiso superuser.

### 4. Race conditions
- `generate_invoice_number` → envolver en transacción atómica con lock (`select_for_update()` sobre la última fila, o generar el número dentro de una transacción con retry en IntegrityError).
- `SiteConfiguration` → forzar singleton: `save()` que no cree duplicados (pk=1 o validación), `get_instance()` con `get_or_create(pk=1)`.

## Criterios de aceptación

- [ ] `SoftDeleteManager` existe; `Model.objects.all()` no devuelve soft-deleted; `all_objects` sí.
- [ ] Listados comerciales, exports CSV, admin y API pública no muestran borrados.
- [ ] Soft delete NO borra archivos físicos; hard delete SÍ.
- [ ] `Warning` tiene `record_active` y su delete es soft.
- [ ] `generate_invoice_number` no duplica bajo concurrencia (test con dos threads o transacciones).
- [ ] `SiteConfiguration` singleton: no pueden existir 2 filas.
- [ ] `python manage.py check` y `python manage.py test` pasan (ajustar tests que asumían borrados visibles).
