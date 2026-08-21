# 088 · Seguridad crítica — Plan

## Enfoque

6 frentes independientes de seguridad. Prioridad: credenciales y fuga de datos primero; ASGI y open redirect son fixes de una línea; email backend se elimina.

## Implementación

1. **FTP credentials** — crear settings holder para `FTP_OBS_HOST/USER/PASS`; modificar `FileObs.py` para recibirlas por constructor; actualizar la vista que instancia `FileObs`; actualizar `generate_env.py` y `env.sample`; actualizar `.secrets.baseline` si aplica.
2. **Rate limiting** — agregar `DEFAULT_THROTTLE_CLASSES` en settings REST_FRAMEWORK; verificar con tests.
3. **Auth endpoints** — `ExcelJSONView` con LoginRequired + permiso; `ajax_pending_subscriptions` con login + ownership check; `django-ratelimit` en proxys/imágenes (o throttle manual por IP en DescargarGifView).
4. **ASGI** — typo fix de una línea.
5. **Open redirect** — helper de validación de `next` en login.
6. **Email backend (certificado autofirmado)** — mantener `config/custom_email_backend.py` (el correo del proyecto usa certificado autofirmado); `settings.py` ya lee `EMAIL_BACKEND` desde env; `generate_env.py` lo escribe apuntando al backend custom cuando el correo es autofirmado. `EMAIL_USE_TLS=True` se mantiene. Además, `generate_env.py` se vuelve interactivo (prod/dev + valores reales).

## Riesgos

- `FileObs.py` puede importar settings desde un paquete que no espera Django settings → probar import en la vista.
- Quitar `csrf_exempt` de ExcelJSONView puede romper el JS cliente que lo consume → verificar el template/JS que lo llama.
- Rate limiting en proxys: no romper el portal público (usar límites generosos, ej. 300/h IP).

## Verificación

- `python manage.py check`
- `python manage.py test apps.api apps.meteo apps.commercial apps.user_auth apps.core`
- Test manual: request anónimo >100/h a `/api/stations/` → 429.
- `grep -r "CasaB2024" .` → sin resultados (excepto git history).
