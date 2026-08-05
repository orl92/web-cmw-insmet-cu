# 081 — tasks

- [ ] **T1** Estado base: renderizar `home:index` + `home` otros (modelos/satélites/servicios/institucion) con test client; registrar 200 y capturar HTML para comparar después.
- [ ] **T2** Footer (footer.html): unificar los dos `<footer class="footer">` en uno.
- [ ] **T3** Footer: eliminar `rel="noreferrer"` duplicado (línea ~83).
- [ ] **T4** Footer: reemplazar `document.write(new Date().getFullYear())` por `{% now 'Y' %}`.
- [ ] **T5** Navbar (navbar.html): quitar el wrapper `navbar-nav flex-row order-md-last` anidado (líneas 14-15).
- [ ] **T6** Navbar: borrar el bloque `{% comment %}` de notificaciones (líneas 37-67).
- [ ] **T7** Navbar: cambiar brand `<h1>` (línea 9) a `div`/`a` no-heading.
- [ ] **T8** Investigar forecast_region_card.html: confirmar si `region_data` siempre acompaña a `latest_forecast` en las vistas del home; añadir guard si no es seguro.
- [ ] **T9** empty_state.html: añadir rama `{% else %}` con icono por defecto para valores desconocidos.
- [ ] **T10** Verificación: `python manage.py check`; test client 200 en páginas públicas; comparar con el HTML de T1 (no debe romper estructura); `python manage.py test` si aplica.
- [ ] **T11** Actualizar `spec/constitution/roadmap.md` (mover a "Hecho") y commit descriptivo (081).
