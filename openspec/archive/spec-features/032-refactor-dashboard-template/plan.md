# Plan — 032-refactor-dashboard-template

## Enfoque técnico
Crear `templates/includes/dashboard/` con 5 archivos:

| Include | Contenido origen | Líneas |
|---------|-----------------|--------|
| superuser_kpis.html | Stats staff + grupos + logins + modales | 7-462 |
| alertas_activas.html | Alertas tempranas, ciclones, tormentas | 465-736 |
| cliente_suscripciones.html | Suscripciones cliente + facturas | 738-833 |
| resumen_comercial.html | Cards analytics + income range + modal subs | 835-1008 |
| pronosticos.html | Regiones + chart temperaturas | 1010-1274 |

Crear `templates/includes/pagination.html` parametrizado con `page_obj`.

JS inline (1280-1583) y CSS inline (1584-1666) permanecen en dashboard.html.

Cada include lleva sus propios `{% load %}` (static, my_filters, home_extras).

## App(s) modificada(s)
- templates/pages/dashboard/dashboard.html

## Archivos nuevos
- templates/includes/dashboard/superuser_kpis.html
- templates/includes/dashboard/alertas_activas.html
- templates/includes/dashboard/cliente_suscripciones.html
- templates/includes/dashboard/resumen_comercial.html
- templates/includes/dashboard/pronosticos.html
- templates/includes/pagination.html
