# Spec — 063-templates-static

## Criterios de Aceptación

1. Todas las ListViews del dashboard tienen `paginate_by = 20`.
2. Las ListViews de home que listan colecciones grandes tienen
   `paginate_by` definido.
3. No hay bloques HTML/JS comentados en templates de producción.
4. Todas las `<img>` tienen atributo `alt` descriptivo.
5. Los formularios tienen `aria-label` o `<label>` asociado.
6. No se rompen tests.
