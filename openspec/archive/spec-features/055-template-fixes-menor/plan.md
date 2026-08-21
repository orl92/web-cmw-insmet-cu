# Plan — Feature 055

## Enfoque técnico

- Cambios aislados en 4 archivos. No requieren migraciones.
- El logo SVG se extrae a `templates/includes/logo.html` y se incluye desde navbar.html y sign-in.html.

## Archivos

| Archivo | Cambio |
|---------|--------|
| `templates/pages/home/pago/pago_qr.html` | `execCommand('copy')` → `clipboard.writeText()` |
| `templates/layouts/avisos.html` | Agregar `aria-label` a botones PDF nav |
| `templates/pages/home/satelites/satelites.html` | Corregir `<figcaption>` huérfano (agregar `<figure>` o cambiar a `<div>`) |
| `templates/includes/logo.html` | Nuevo: SVG del logo CMW extraído |
| `templates/includes/home/navbar.html` | Reemplazar SVG inline por `{% include %}` |
| `templates/pages/login/sign-in.html` | Reemplazar SVG inline por `{% include %}` |
