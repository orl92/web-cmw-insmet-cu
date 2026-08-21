# 089 · Operación en producción — Plan

## Enfoque

5 frentes independientes de operación. Prioridad: dependencias (crashea hoy), Huey (correos muertos hoy), fail-closed (riesgo silencioso), proxy headers (login roto en prod), gunicorn root.

## Implementación

1. **Deps** — agregar `whitenoise` y `gunicorn` a requirements con versión fija; instalar; probar `PRODUCTION=true`.
2. **Proxy headers** — `SECURE_PROXY_SSL_HEADER` + política de headers modernos; test con header simulado.
3. **Huey ready()** — importar tasks en `apps/core/apps.py` (y las apps con tareas); verificar registro.
4. **Fail-closed** — guard de variables obligatorias en settings cuando `PRODUCTION` o `DEBUG=False`; DEBUG default seguro.
5. **Gunicorn** — quitar root del script; documentar usuario dedicado como mejora futura.

## Riesgos

- Cambiar `DEBUG` default puede romper entornos que dependían del default silencioso → revisar que CI y dev pasen.
- Importar tasks en `ready()` puede duplicar imports si ya se importan en vistas → verificar que el import sea idempotente (Python lo es por módulo).
- `SECURE_PROXY_SSL_HEADER` en entorno sin proxy puede romper detección de HTTPS si un atacante manda el header → documentar que solo aplica detrás de Nginx (confianza en el proxy).

## Verificación

- `python manage.py check`
- `python manage.py test`
- `PRODUCTION=true python manage.py collectstatic --no-input` (con whitenoise instalado)
- `huey_consumer config.huey.huey` por 5s → loguea tareas registradas
- Sin `.env` con `PRODUCTION=true python manage.py check` → `ImproperlyConfigured` esperado
