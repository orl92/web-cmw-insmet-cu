# 080 — debug-toolbar

## Motivación

No hay herramienta de profiling en desarrollo. Para diagnosticar N+1 queries, rendimiento de templates y uso de caché, es necesario `django-debug-toolbar`.

## Alcance

- Agregar `django-debug-toolbar` a `requirements.txt` (dev only)
- Configurar en `settings.py` (solo `DEBUG=True`)
- Configurar URLs en `config/urls.py`
- Documentar en AGENTS.md

## Criterios de Aceptación

1. Toolbar visible en desarrollo, no en producción
2. Panels: SQL, Cache, Templates, Signals, Requests
3. `python manage.py check` sin errores
