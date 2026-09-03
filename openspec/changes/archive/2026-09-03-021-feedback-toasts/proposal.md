# Change Proposal: 021-feedback-toasts — Mensajes de feedback como toasts

## Motivación (Problem)

El usuario pidió unificar el estilo de feedback del portal. Hoy las ~121 llamadas a
`django.contrib.messages` (success/error/warning/info) se renderizan como **alerts
Bootstrap fijos** (`.alert.alert-* alert-dismissible`) apilados arriba del contenido en
`dashboard.html` y `home.html`. El patrón de toast que ya se usa en el toggle de
mantenimiento de la configuración (`showToast` + `#toast-container`) le gustó más: es
discreto, apilable en la esquina, autodesaparece y permite cierre manual.

Romper esa brecha de UX **sin** tocar la API estándar de Django ni las vistas.

## Solución

Mantener intactas todas las llamadas `messages.*` en Python (y su uso por el middleware).
Cambiar únicamente el **render**: reemplazar los bloques `{% for message in messages %}`
de `dashboard.html` y `home.html` para que cada mensaje se convierta en un **toast**
server-side con el mismo markup que produce `showToast`:

- Reutiliza `#toast-container` e `include utils.html` ya existentes en `base.html`.
- Mapeo de tags: `message.level_tag` → `success|danger|warning|info`; si
  `message.extra_tags` contiene `'danger'`, forzar `danger`.
- `escapejs` en `message`/`level_tag`/`tags` como guarda contra romper el `<script>`
  inline y contra XSS (además del escape que ya hace `showToast`).
- Duración 5000 ms (default de `showToast`), con botón de cierre.
- Los mensajes posteriores a redirect (middleware de perfil/mantenimiento, login/logout)
  llegan al nuevo page load vía sesión y se muestran correctamente.

No se modifican vistas Python, middleware, ni `utils.html`.

## Criterios de aceptación

- [ ] Los mensajes de feedback (success/error/warning/info) de todas las apps se muestran
      como toasts en `#toast-container`, no como alerts fijos.
- [ ] El mapping de tags es correcto: success→success, error→danger, warning→warning,
      info→info, y `extra_tags='danger'` fuerza danger.
- [ ] Un mensaje con `'`, `"` o `</script>` en su texto no rompe la página (escapejs).
- [ ] Tras un redirect (ej. perfil incompleto, login OK, mantenimiento activado) el toast
      se muestra en la siguiente carga.
- [ ] Los toasts autodesaparecen (~5 s) y tienen botón de cierre.
- [ ] djlint limpio, `manage.py check` 0 issues, suite de tests en verde, sin tocar
      ninguna llamada Python de `messages.*`.

## No go (fuera de alcance)

- No cambiar el texto de ningún mensaje existente.
- No tocar `middleware.py`, vistas, ni la API `messages.*`.
- No migrar a nonces CSP (queda anotado en backlog) ni reeemplazar `initAutoDismissAlerts`.
