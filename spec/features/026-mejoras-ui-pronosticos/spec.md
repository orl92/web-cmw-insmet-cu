# 026 · Mejoras UI pronósticos

**Estado:** completado

## Qué hace

Reestructura la interfaz de la lista de pronósticos y corrige el layout responsivo del formulario de crear/editar.

## Criterios de aceptación

- [x] Tablas (pronóstico, extendido, astronomía) visibles con headers y mensaje "No hay datos" cuando no hay pronósticos para la fecha
- [x] Botones de acción (CSV, Excel, Editar, Eliminar) como `btn-icon` cuadrados, solo icono, tooltips abajo
- [x] Botones editar/eliminar movidos del footer de cada tarjeta al header (junto a CSV/Excel)
- [x] Botón "Añadir Pronóstico" solo visible cuando no hay datos
- [x] En móvil: tarjetas de pronóstico extendido apiladas verticalmente (no comprimidas)
- [x] `python manage.py check` — sin errores
- [x] `python manage.py test` — 136 tests pasan
