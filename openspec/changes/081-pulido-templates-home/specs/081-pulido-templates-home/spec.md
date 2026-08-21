# Spec — 081-pulido-templates-home

## Criterios de Aceptación

1. El footer renderiza una sola banda `<footer>`; sin `document.write`, sin `rel` duplicado.
2. El navbar público no tiene wrappers anidados redundantes ni código comentado; el brand no es `h1`.
3. Cada página pública mantiene un único `h1` real de encabezado de página.
4. `python manage.py check` sin errores y render de `home:index` con 200 (test client con ALLOWED_HOSTS que incluya `testserver`).
5. Sin regresión visual en desktop/móvil (verificación manual o de pantalla).
