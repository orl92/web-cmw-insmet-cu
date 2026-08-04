# 081 — pulido-templates-home

## Motivación

Revisión de calidad sobre las templates del portal público (`templates/includes/home/` y `templates/layouts/home.html`) detectó HTML inválido, estructura de encabezados incorrecta y componentes redundantes que degradan el markup y la accesibilidad sin aporte visual.

## Alcance

- **Footer** (`templates/includes/home/footer.html`):
  1. Unificar los dos `<footer class="footer">` (líneas 2 y 100) en uno solo para evitar la costura visible entre bandas.
  2. Quitar `rel` duplicado en el enlace de GitHub (línea 83: `rel="noopener noreferrer" rel="noreferrer"`).
  3. Reemplazar `document.write(new Date().getFullYear())` (línea 142) por `{% now 'Y' %}`.
- **Navbar** (`templates/includes/home/navbar.html`):
  4. Quitar el wrapper anidado redundante `navbar-nav flex-row order-md-last` (líneas 14-15).
  5. Eliminar el bloque `{% comment %}` de notificaciones (líneas 37-67), código muerto.
  6. Cambiar el brand de `<h1>` (línea 9) a un elemento no-heading (div/a), porque el header de página ya emite `<h2 class="page-title">` y el `h1` de marca rompe la jerarquía.
- **Investigar** (validar antes de tocar):
  7. `forecast_region_card.html:6-7` — `region_data.morning/.afternoon/.night` se desreferencia con guard solo de `latest_forecast`; confirmar que las vistas del home siempre setean ambos juntos.
  8. `empty_state.html` — sin rama `{% else %}`/fallback cuando `icon` no está en `{forecast, astronomy, astronomy_sun, uv}`.

## Fuera de alcance

- Cambios de contenido, estilos o comportamiento en `home.js`, vistas o datos.
- Refactor de las templates del dashboard (`templates/includes/dashboard/`).

## Criterios de Aceptación

1. El footer renderiza una sola banda `<footer>`; sin `document.write`, sin `rel` duplicado.
2. El navbar público no tiene wrappers anidados redundantes ni código comentado; el brand no es `h1`.
3. Cada página pública mantiene un único `h1` real de encabezado de página.
4. `python manage.py check` sin errores y render de `home:index` con 200 (test client con ALLOWED_HOSTS que incluya `testserver`).
5. Sin regresión visual en desktop/móvil (verificación manual o de pantalla).
