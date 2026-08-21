# Spec — 034-refactor-templatetags

## Criterios de aceptación
- Filtros divididos en 4 submódulos (form, meteo, perm, utils)
- `my_filters.py` re-exporta todos (no cambia {% load my_filters %})
- `in_group_permissions` eliminado (0 usos confirmados)
- `id="example"` → `id="{{ list_id|default:'example' }}"`
- `python manage.py test dashboard` pasa
