# 047 — URL consistency (trailing slashes)

## Qué hace
Corrige URLs de delete que no tienen trailing slash, inconsistentes con el resto del proyecto.

**Archivo:** `accounts/urls.py:30,35`
```python
path('group/delete/<uuid:uuid>', ...)      # sin trailing slash
path('user/delete/<uuid:uuid>', ...)       # sin trailing slash
```
Todas las demás URLs del proyecto tienen trailing slash.

## Criterios de aceptación
- `group/delete/<uuid:uuid>/` con trailing slash
- `user/delete/<uuid:uuid>/` con trailing slash
- Tests pasan
