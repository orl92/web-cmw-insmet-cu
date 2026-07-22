# Feature 052 — Refactor modal PDF (eliminar duplicación)

## Qué hace
El modal fullscreen de visualización de PDF (~35 líneas de HTML) está copiado literalmente en 7+ templates. Se extrae a un partial reutilizable.

## Criterios de aceptación

1. El modal PDF existe una sola vez en `templates/includes/home/pdf_modal.html`.
2. Los 7 templates que lo usan lo incluyen con `{% include 'includes/home/pdf_modal.html' %}`.
3. El modal funciona igual que antes (mismos botones, mismas clases, mismo comportamiento).
