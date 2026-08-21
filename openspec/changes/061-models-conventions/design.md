# Plan — 061-models-conventions

## Estrategia

1. **FileHandlerMixin en Invoice y Certificate**
   - Agregar `FileHandlerMixin` a la herencia de `Invoice` y `Certificate`.
   - Definir `file_fields = ['pdf']` en cada uno.
   - Verificar que el `delete()` de SoftDeleteModel + FileHandlerMixin no
     entre en conflicto (el orden de herencia debe ser
     `(SoftDeleteModel, FileHandlerMixin, models.Model)`).

2. **Meta.ordering faltante**
   - Agregar `ordering` a `InvoiceItem` y `WeatherReport`.
   - Agregar `ordering` a los Meta de `EarlyWarning`, `TropicalCyclone`,
     `StormWarning` (o heredarlo si BaseWarning lo definiera como abstract).

3. **related_name explícito**
   - `BaseWarning.user` → `related_name="%(class)s_warnings"`
   - `InvoiceItem.subscription` → `related_name="invoice_items"`

4. **SiteConfiguration**
   - Eliminar `id = models.AutoField(primary_key=True)` (Django ya lo pone).

## Orden recomendado

1. FileHandlerMixin en Invoice y Certificate (más crítico: archivos huérfanos)
2. Meta.ordering (bajo riesgo)
3. related_name (puede romper queries existentes, requiere búsqueda)
4. SiteConfiguration cleanup

## Riesgos

- Cambiar related_name puede romper referencias en views/forms/templates.
  Buscar con grep antes de renombrar.
- FileHandlerMixin combinado con SoftDeleteModel: el orden de herencia debe
  ser correcto; probar que `hard_delete()` aún limpia archivos.
- Migraciones: aunque no versionadas, verificar que `makemigrations` no
  produzca cambios inesperados.
