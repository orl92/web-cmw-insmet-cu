# 063 — templates-static

## Motivación

Los templates del proyecto tienen varios problemas detectados: 13 de 15
ListViews del dashboard no tienen `paginate_by = 20`, hay templates que
podrían contener JS/CSS inline no externalizado, y no se ha auditado la
accesibilidad (alt text en imágenes, aria labels, contraste). Además,
posibles bloques comentados arrastrados de desarrollo que nunca se
limpiaron.

## Alcance

- `templates/pages/dashboard/**/*.html` (list views, forms, detail)
- `templates/pages/home/**/*.html` (páginas públicas)
- `templates/layouts/*.html`
- `apps/dashboard/views/**/views.py` (ListViews sin paginate_by)
- `apps/home/views/**/views.py` (verificar paginate_by)

## Criterios de Aceptación

1. Todas las ListViews del dashboard tienen `paginate_by = 20`.
2. Las ListViews de home que listan colecciones grandes tienen
   `paginate_by` definido.
3. No hay bloques HTML/JS comentados en templates de producción.
4. Todas las `<img>` tienen atributo `alt` descriptivo.
5. Los formularios tienen `aria-label` o `<label>` asociado.
6. No se rompen tests.
