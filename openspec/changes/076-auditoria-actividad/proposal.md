# 076 — auditoria-actividad

## Motivación

No hay registro centralizado de actividad de usuarios. Las acciones críticas (crear factura, cancelar suscripción, eliminar cliente) solo quedan en mensajes flash que se pierden al cerrar sesión.

## Alcance

- Modelo `ActivityLog` con: usuario, acción, modelo, objeto_id, timestamp, IP, detalles
- Middleware opcional para registrar accesos a vistas
- Vista de log para superusers con filtros (fecha, usuario, acción)
- Integrar con `log_action()` existente

## Criterios de Aceptación

1. Cada acción comercial (crear/actualizar/eliminar) queda registrada en ActivityLog
2. Vista de log accesible a superusers con paginación y filtros
3. `python manage.py test` pasa
