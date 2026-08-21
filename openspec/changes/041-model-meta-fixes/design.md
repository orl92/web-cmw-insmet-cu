# Plan — 041-model-meta-fixes

## Enfoque técnico
1. Agregar `ordering` a los modelos faltantes (por nombre, fecha, etc.)
2. Agregar `default_permissions = ()` + 4 permisos custom a Contract
3. Agregar validación en `CompanySettings.clean()` o `save()` que prevenga segundo objeto
4. Ejecutar `makemigrations`

## App(s) modificadas
- dashboard/models.py
