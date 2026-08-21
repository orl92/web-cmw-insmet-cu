# Spec — 035-migrar-is-staff

## Criterios de aceptación
- `list.html` usa `{% if request.user.is_staff %}` en vez de `{% if is_staff %}`
- Las 21 vistas no pasan `context['is_staff']`
- Funcionalidad idéntica (request.user.is_staff es True para staff y superuser)
- Tests pasan
