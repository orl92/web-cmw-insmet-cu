# Plan — 039-remover-load-sin-usar

## Enfoque técnico
1. Leer `alertas_activas.html` para confirmar que no usa filtros de `my_filters`
2. Eliminar `{% load my_filters %}`
3. Tests pasan

## App(s) modificada(s)
- templates/includes/dashboard/alertas_activas.html
