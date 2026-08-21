# Feature 051 — Fixes templates de autenticación

## Qué hace
Corrige dos problemas en templates del flujo de login: lang incorrecto y falta de autocomplete en inputs de credenciales.

## Criterios de aceptación

1. `templates/layouts/base-auth.html` usa `<html lang="es">` en vez de `lang="en"`.
2. Los inputs de username y password en `templates/pages/login/sign-in.html` tienen `autocomplete="username"` y `autocomplete="current-password"` respectivamente.
