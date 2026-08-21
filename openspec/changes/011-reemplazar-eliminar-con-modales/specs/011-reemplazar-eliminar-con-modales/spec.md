# Spec — 011-reemplazar-eliminar-con-modales

## Criterios de aceptación

- [ ] Cada listado con acción de eliminar tiene un botón 🗑️ que abre un modal de confirmación.
- [ ] El modal muestra "¿Estás seguro de que deseas eliminar este elemento?" y "Esta acción no tiene vuelta atrás."
- [ ] Confirmar en el modal envía POST al endpoint de eliminación correspondiente.
- [ ] Cancelar o hacer clic fuera del modal lo cierra sin enviar nada.
- [ ] No hay páginas de confirmación independientes (se eliminan los 17 templates viejos).
- [ ] Todas las vistas DeleteView se convierten a View (POST-only) y funcionan correctamente.
- [ ] `python manage.py check` y `python manage.py test` pasan sin errores.
