# Plan — 034-refactor-templatetags

## Enfoque técnico
my_filters.py se mantiene como módulo público que re-exporta:

| Submódulo | Filtros |
|-----------|---------|
| form_filters.py | add_class, add_attrs, filename |
| meteo_filters.py | get_tiempo_description, get_mar_description, get_luna_description, get_sol_description, get_weather_img_*, get_moon_img, get_sun_img, get_forecast_day, period_display, remove_images_and_special_chars |
| perm_filters.py | has_permission, get_model_verbose_name, get_permission_type_from_codename, filter_permissions_by_type, group_permissions_for_table, group_permissions_for_modal, get_permission_verb, get_permission_badge_class, get_permission_checkbox_class |
| utils_filters.py | get_dict_value, action_description, get_icon_for_action, time_since |

my_filters.py queda:
```python
from .form_filters import *
from .meteo_filters import *
from .perm_filters import *
from .utils_filters import *
```
(sin in_group_permissions)

En list.html: `id="example"` → `id="{{ list_id|default:'example' }}"`.
En list.html extrajs: DataTable selector igual.

## App(s) modificada(s)
- dashboard/templatetags/
- templates/layouts/list.html

## Archivos nuevos
- dashboard/templatetags/form_filters.py
- dashboard/templatetags/meteo_filters.py
- dashboard/templatetags/perm_filters.py
- dashboard/templatetags/utils_filters.py
