# Plan — Feature 051

## Enfoque técnico

- Solo cambios en 2 templates.
- No requiere migraciones, cambios de modelo ni tests especializados.

## Archivos

| Archivo | Cambio |
|---------|--------|
| `templates/layouts/base-auth.html:11` | `lang="en"` → `lang="es"` |
| `templates/pages/login/sign-in.html` | Agregar `autocomplete="username"` al input username (línea ~84) y `autocomplete="current-password"` al input password (línea ~96) |
