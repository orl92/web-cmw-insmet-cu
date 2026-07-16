# 011 · Reemplazar páginas de eliminación por modales

**Estado:** implementado

## Qué hace

Reemplaza las 17 páginas independientes de confirmación de eliminación (vistas DeleteView con template propio) por modales Bootstrap reutilizables. Cada listado en el dashboard tendrá un botón con icono de papelera que abre un modal de confirmación; al confirmar, se envía el POST vía JavaScript.

## Por qué

- Elimina ~17 templates duplicados que solo muestran un mensaje de confirmación.
- Mejora la experiencia de usuario: la confirmación es inline, sin cambiar de página.
- Centraliza la lógica del modal de borrado en dos partials reutilizables.
- Simplifica las vistas DeleteView convirtiéndolas a View (POST-only), eliminando `template_name`, `model` y `get_context_data`.

## Criterios de aceptación

- [ ] Cada listado con acción de eliminar tiene un botón 🗑️ que abre un modal de confirmación.
- [ ] El modal muestra "¿Estás seguro de que deseas eliminar este elemento?" y "Esta acción no tiene vuelta atrás."
- [ ] Confirmar en el modal envía POST al endpoint de eliminación correspondiente.
- [ ] Cancelar o hacer clic fuera del modal lo cierra sin enviar nada.
- [ ] No hay páginas de confirmación independientes (se eliminan los 17 templates viejos).
- [ ] Todas las vistas DeleteView se convierten a View (POST-only) y funcionan correctamente.
- [ ] `python manage.py check` y `python manage.py test` pasan sin errores.

## Fuera de alcance

- Reemplazar otros modales de confirmación (crear/editar) — solo eliminación.
- Cambiar la lógica de negocio del borrado (log_action, permisos, etc.).
