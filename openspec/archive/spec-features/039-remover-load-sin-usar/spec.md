# 039 — Remover {% load %} sin usar en alertas_activas.html

## Qué hace
Elimina `{% load my_filters %}` de `templates/includes/dashboard/alertas_activas.html` porque el template no usa ningún filtro de ese módulo.

## Criterios de aceptación
- `alertas_activas.html` no tiene `{% load my_filters %}`
- Funcionalidad idéntica
