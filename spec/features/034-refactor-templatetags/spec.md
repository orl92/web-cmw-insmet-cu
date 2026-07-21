# 034 — Refactor Templatetags y limpieza

## Qué hace
Divide `dashboard/templatetags/my_filters.py` (703 líneas, 30 filtros) en
submódulos por dominio. Elimina filtro muerto. Parametriza `id="example"`
en DataTable para soportar múltiples tablas.

## Criterios de aceptación
- Filtros divididos en 4 submódulos (form, meteo, perm, utils)
- `my_filters.py` re-exporta todos (no cambia {% load my_filters %})
- `in_group_permissions` eliminado (0 usos confirmados)
- `id="example"` → `id="{{ list_id|default:'example' }}"`
- `python manage.py test dashboard` pasa
