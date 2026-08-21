# Spec — 050-xss-safe-content

## Criterios de aceptación

1. Los 4 templates que usan `|safe` en campos rich-text ya no lo usan directamente.
2. Se crea un template tag o filtro personalizado que sanitiza permitiendo solo HTML seguro (párrafos, negritas, listas, enlaces).
3. El contenido se ve igual visualmente que antes (negritas, listas, saltos de línea se conservan).
4. Tags peligrosos (`<script>`, `<iframe>`, `<style>`, `onerror=`, etc.) se eliminan.
