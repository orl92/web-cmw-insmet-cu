# Tasks — 089-operacion-produccion

## Dependencias de producción

- [x] `requirements.txt` — Agregar `whitenoise` y `gunicorn` con versiones fijas.
- [x] `pip install -r requirements.txt` — Instalar y verificar import: `python -c "import whitenoise, gunicorn"`.
- [x] Verificar `PRODUCTION=true python manage.py collectstatic --no-input` y `PRODUCTION=true python manage.py check`.

## Headers de seguridad tras proxy

- [x] `config/settings.py` — Agregar `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`.
- [x] `config/settings.py` — Evaluar `SECURE_SSL_REDIRECT` (dejar False si Nginx lo maneja; documentar en comentario).
- [x] `config/settings.py` — Agregar `SECURE_REFERRER_POLICY = 'same-origin'` y `SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'`.
- [x] `config/settings.py` — Evaluar/reemplazar `SECURE_BROWSER_XSS_FILTER` (deprecado en Django 5.x).
- [x] Test: request con `HTTP_X_FORWARDED_PROTO=https` → `request.is_secure()` True y cookie secure set.

## Registro de tareas Huey

- [x] `apps/core/apps.py` — Importar `from apps.core import tasks` (u otro mecanismo) en `ready()`.
- [x] Revisar otras apps con tareas (commercial, meteo, user_auth) e importarlas igualmente.
- [x] Verificar: `huey_consumer config.huey.huey` registra las tareas (log de arranque o inspección).
- [ ] (Alternativa si ready() falla) Importar tasks en `config/huey.py`.

## Fail-closed sin `.env`

- [x] `config/settings.py` — Agregar guard: si `IS_PRODUCTION` (o `DEBUG` explícitamente False) y faltan `SECRET_KEY`/`DB_*`, lanzar `ImproperlyConfigured` con mensaje claro.
- [x] `config/settings.py:21` — `DEBUG` default → `False` (o `os.getenv('DEBUG', 'False')`), nunca `'True'`.
- [x] Mantener `get_random_secret_key()` solo para dev.
- [x] Test: sin `.env` con `PRODUCTION=true` → `ImproperlyConfigured`.

## Gunicorn sin root

- [x] `gunicorn.sh` — Ejecutar como el usuario del sistema que posee el venv (no root); quitar `USER=root/GROUP=root`.
- [x] `README.md` — Actualizar ejemplo de Supervisor con el usuario correcto.
- [x] `README.md` — Documentar mejora futura: usuario dedicado `webcmp` + chown (roadmap backlog).

## Verificación

- [x] `python manage.py check`
- [x] `python manage.py test`
- [ ] Actualizar roadmap.md (mover 089 a Hecho al completar).
- [ ] Commit.
