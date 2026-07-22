# Feature 055 — Fixes menores en templates

## Qué hace
Corrige 4 problemas menores en distintos templates: API deprecada, accesibilidad, HTML semántico y duplicación de SVG.

## Criterios de aceptación

1. `pago_qr.html` usa `navigator.clipboard.writeText()` en vez de `document.execCommand('copy')`.
2. `avisos.html` los botones de navegación PDF (`‹`, `›`, `-`, `+`) tienen `aria-label` descriptivo.
3. `satelites.html` no tiene `<figcaption>` sin `<figure>` padre.
4. El SVG del logo (CMW) no está duplicado entre navbar.html y sign-in.html.
