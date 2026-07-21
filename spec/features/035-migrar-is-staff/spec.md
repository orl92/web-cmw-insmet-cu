# 035 — Migrar is_staff contextual a request.user.is_staff

## Qué hace
Reemplaza la variable `is_staff` (seteada manualmente en 21 vistas) por
`request.user.is_staff` directo en el template. Elimina ~42 líneas de
código redundante en las vistas.

## Criterios de aceptación
- `list.html` usa `{% if request.user.is_staff %}` en vez de `{% if is_staff %}`
- Las 21 vistas no pasan `context['is_staff']`
- Funcionalidad idéntica (request.user.is_staff es True para staff y superuser)
- Tests pasan
