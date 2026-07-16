# 012 · Tests automatizados

**Estado:** implementado

## Qué hace

Reemplaza los 6 stubs de `tests.py` (uno por app) con tests reales organizados en subdirectorios `tests/` con `__init__.py`. Cubre modelos, vistas, formularios, API endpoints y utilities.

## Por qué

- Sin tests no es posible refactorizar con seguridad (features 013, 014).
- El proyecto tiene 0% de cobertura actualmente.
- Los tests existentes son stubs vacíos que pasan trivialmente.

## Criterios de aceptación

- [ ] `python manage.py test accounts` — mínimo 15 tests, todos pasan
- [ ] `python manage.py test dashboard` — mínimo 30 tests, todos pasan
- [ ] `python manage.py test api` — mínimo 6 tests, todos pasan
- [ ] `python manage.py test home` — mínimo 6 tests, todos pasan
- [ ] `python manage.py test common` — mínimo 4 tests, todos pasan
- [ ] `python manage.py test login` — mínimo 2 tests, todos pasan
- [ ] `python manage.py test` corre todos los tests sin errores
- [ ] No se rompe ninguna funcionalidad existente

## Fuera de alcance

- Tests de integración con servicios externos (LDAP, API de modelos, satélites)
- Tests de generación de PDF (depende de wkhtmltopdf/pdfkit en el sistema)
- Tests de middleware de mantenimiento (requiere configuración especial)
- Tests de management commands personalizados
- Cobertura > 80% (se busca cobertura base, no exhaustiva)
