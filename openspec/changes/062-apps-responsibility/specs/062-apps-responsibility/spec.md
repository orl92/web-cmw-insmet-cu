# Spec — 062-apps-responsibility

## Criterios de Aceptación

1. Feature spec creada para cada nuevo dominio extraído (geografía,
   facturación, CRM, correos).
2. Cada nueva app tiene su propio `models.py`, `views/`, `forms/`, `urls.py`,
   `tests/`.
3. Las vistas del dashboard referencian las nuevas apps mediante imports.
4. No se rompe ninguna URL existente (redirecciones o compatibilidad).
5. Tests existentes pasan.
