# Feature 089 · Operación en producción

## Motivación

Auditoría de configuración de producción encontró 5 problemas que rompen o degradan el deploy real:

1. **`whitenoise` y `gunicorn` NO están en `requirements.txt`** — `config/settings.py:110,254,320-324` referencian whitenoise y `gunicorn.sh:17` ejecuta gunicorn, pero el venv limpio con solo `requirements.txt` no los tiene. `PRODUCTION=true` (modo documentado en README/AGENTS.md) crashea al primer request o en `collectstatic`. CI no lo detecta porque corre sin `PRODUCTION`.
2. **`SECURE_PROXY_SSL_HEADER` faltante** — Nginx termina TLS y manda `X-Forwarded-Proto` (README.md:166), pero Django no lo interpreta. Con `SESSION_COOKIE_SECURE=True` y `CSRF_COOKIE_SECURE=True` (settings.py:53-54), `request.is_secure()` es False tras el proxy → las cookies seguras nunca se setean; login/CSRF rotos. Además `SECURE_SSL_REDIRECT = False` deja HTTPS a merced de Nginx.
3. **Worker Huey con 0 tareas registradas** — `apps/core/apps.py:9-10` (`ready()` es `pass`); `apps/core/tasks.py` solo se importa desde vistas (`core/utils.py:81`, `commercial/views/invoices.py:30`). `huey_consumer config.huey.huey` (`run_huey.sh:9`) importa únicamente `config/huey.py` → tareas de correo/PDF nunca se procesan en producción. Violación del checklist de AGENTS.md.
4. **Fallback silencioso y peligroso sin `.env`** — sin `.env`, settings arranca con SQLite (`settings.py:146` por `DEBUG` default `'True'` línea 21), `DEBUG=True`, `SECRET_KEY` aleatoria por boot (líneas 37-46), sin error. En producción esto es un desastre silencioso.
5. **Gunicorn como root** — `gunicorn.sh:6-7` (`USER=root, GROUP=root`), repetido en README.md:220-221,252. Cualquier compromiso de la app es compromiso total del host.

## Solución

### 1. Dependencias de producción
- Agregar `whitenoise` y `gunicorn` a `requirements.txt` (pinned).
- Actualizar `requirements-dev.txt` si hace falta.
- Verificar que `PRODUCTION=true python manage.py collectstatic` funcione.

### 2. Headers de seguridad tras proxy
- Agregar `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` en settings (solo cuando hay proxy; documentar).
- Evaluar `SECURE_SSL_REDIRECT` (dejarlo en False si Nginx lo maneja, documentándolo).
- Evaluar headers faltantes: `SECURE_REFERRER_POLICY`, `SECURE_CROSS_ORIGIN_OPENER_POLICY`, y reemplazar `SECURE_BROWSER_XSS_FILTER` (deprecado en Django 5.x) por la política moderna.

### 3. Registro de tareas Huey
- Importar `apps.core.tasks` en `AppConfig.ready()` de `apps/core/apps.py` (y las de otras apps si existen: commercial, meteo, user_auth).
- Verificar que `huey_consumer config.huey.huey` registre las tareas (probar con un log de arranque o `huey` list).
- Alternativa si no conviene ready(): importar tasks en `config/huey.py` directamente.

### 4. Fail-closed sin `.env` en producción
- Si `PRODUCTION` está definido (o `DEBUG` explícitamente `False`) y faltan variables obligatorias (`SECRET_KEY`, `DB_*`), lanzar `ImproperlyConfigured` con mensaje claro.
- Mantener el fallback `get_random_secret_key()` SOLO para desarrollo.
- `DEBUG` sin valor en producción → `False` (nunca default `True`).

### 5. Gunicorn sin root
- `gunicorn.sh` → ejecutar como el usuario del sistema que posee el venv (no root), o crear usuario dedicado `webcmp` documentado en README.
- Actualizar ejemplo de Supervisor en README.
- Documentar como mejora futura: usuario dedicado + chown del directorio (roadmap backlog).

## Criterios de aceptación

- [ ] `pip install -r requirements.txt` instala whitenoise y gunicorn; `PRODUCTION=true` no crashea.
- [ ] `SECURE_PROXY_SSL_HEADER` configurado; cookies seguras funcionan tras proxy (verificable con `request.is_secure()` en un test con `HTTP_X_FORWARDED_PROTO=https`).
- [ ] Tareas Huey registradas: `huey_consumer` loguea las tareas al arrancar (o test de import en `ready()`).
- [ ] Sin `.env` con `PRODUCTION` set → `ImproperlyConfigured` con mensaje claro; sin `.env` en dev → sigue funcionando con secret aleatorio.
- [ ] `gunicorn.sh` no usa root.
- [ ] `python manage.py check` y `python manage.py test` pasan.
