# Spec — 005-servicios-publicos

## Criterios de aceptación

- [x] Listado público de servicios con `service_type='public'`, ordenado por fecha.
- [x] Paginación (10 por página).
- [x] Visor PDF embebido con PDF.js para cada servicio.
- [x] Acceso sin autenticación.
- [x] CRUD en dashboard para gestionar servicios (crear, editar, eliminar) con permisos.
- [x] Validación: servicios públicos requieren PDF; servicios comerciales requieren imagen + código + precio.
