# 073 — ui-polish

## Motivación

Mejoras de experiencia de usuario detectadas durante el desarrollo: falta feedback visual durante cargas asíncronas, notificaciones inconsistentes, y comportamiento responsive irregular en tablas comerciales.

## Alcance

- Loading spinners en DataTables y acciones POST (delete, approve, etc.)
- Unificar sistema de toast/notificaciones con componente Tabler toast
- Auditoría responsive en tablas de commercial (Customer, Invoice, Subscription lists)

## Criterios de Aceptación

1. DataTables muestran spinner mientras carga
2. Acciones POST tienen botón deshabilitado + spinner inline
3. Toasts usan mismo markup Tabler en todas las vistas
4. Tablas commercial tienen scroll horizontal en viewport <768px
5. `python manage.py test` pasa
