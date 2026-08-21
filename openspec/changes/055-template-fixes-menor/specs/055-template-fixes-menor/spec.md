# Spec — 055-template-fixes-menor

## Criterios de aceptación

1. `pago_qr.html` usa `navigator.clipboard.writeText()` en vez de `document.execCommand('copy')`.
2. `avisos.html` los botones de navegación PDF (`‹`, `›`, `-`, `+`) tienen `aria-label` descriptivo.
3. `satelites.html` no tiene `<figcaption>` sin `<figure>` padre.
4. El SVG del logo (CMW) no está duplicado entre navbar.html y sign-in.html.
