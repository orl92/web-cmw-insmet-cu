# Plan — 030-workflow-mejoras

## Enfoque técnico

Feature de documentación/infraestructura. No hay cambios de modelo, vistas, URLs, API, templates ni permisos. Solo se modifica `AGENTS.md`.

## App(s) modificada(s)

- `config/` (AGENTS.md es parte de la documentación del proyecto, no de una app específica)

## Cambios concretos

1. En sección "Entorno y arranque": reemplazar `./run_huey.sh &` por subsección con 3 alternativas.
2. En sección "Testing": reemplazar comando único por política de testing selectivo + creación de tests.
3. En paso 7 de SSD: dividir verificación en check + tests específicos + seguridad.
4. Nuevo checklist "Seguridad post-cambio".
