# 011 · Reemplazar páginas de eliminación por modales — Plan

## Enfoque

Crear dos partials reutilizables (`modal_delete.html` y `modal_delete_js.html`), convertir las 17 vistas DeleteView a View (POST-only), modificar los 17 templates de listado para usar el modal en lugar de enlaces a páginas de confirmación, y eliminar los 17 templates de confirmación antiguos.

## Implementación

1. Crear `templates/includes/dashboard/modal_delete.html` — estructura del modal Bootstrap con header rojo, cuerpo de confirmación y botón Eliminar.
2. Crear `templates/includes/dashboard/modal_delete_js.html` — JavaScript que escucha clics en `.action-btn`, setea la acción del formulario con el UUID, y maneja show/hide del modal.
3. Convertir las 17 vistas DeleteView a View (POST-only) en sus respectivos `views.py`.
4. Modificar los 17 templates de listado: cambiar `<a href>` por `<button class="action-btn">`, añadir includes del modal y JS.
5. Eliminar los 17 templates de confirmación antiguos.

## Decisiones

- **Modal nativo Bootstrap (no htmx/Alpine)** — el proyecto usa Tabler (Bootstrap 5) y Django Templates; no se introducen dependencias.
- **View + POST en vez de DeleteView** — DeleteView requiere `template_name` y `get_context_data` que ya no tienen sentido; un View con `post()` es más simple.
- **UUID en data-atributo** — el UUID se pasa vía `data-uuid` en el botón y se inyecta en la acción del formulario con JavaScript, evitando generar URLs por template tag.
- **Formulario oculto en el modal** — con `display: none` y `{% csrf_token %}`; el JS lo muestra al setear la acción y submittea.

## Riesgos

- **Bootstrap JS nativo vs. manual** — el modal se maneja con JS manual (clases `show`, `modal-backdrop`) en vez de `bootstrap.Modal` para evitar depender de Bootstrap JS bundle. Verificar que funcione correctamente con Tabler.
