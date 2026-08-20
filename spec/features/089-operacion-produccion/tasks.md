# Tasks — 089-operacion-produccion

## Dependencias de producción

- [ ] `requirements.txt` — Agregar `whitenoise` y `gunicorn` con versiones fijas.
- [ ] `pip install -r requirements.txt` — Instalar y verificar import: `python -c "import whitenoise, gunicorn"`.
- [ ] Verificar `PRODUCTION=true python manage.py collectstatic --no-input` y `PRODUCTION=true python manage.py check`.

## Headers de seguridad tras proxy

- [ ] `config/settings.py` — Agregar `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`.
- [ ] `config/settings.py` — Evaluar `SECURE_SSL_REDIRECT` (dejar False si Nginx lo maneja; documentar en comentario).
- [ ] `config/settings.py` — Agregar `SECURE_REFERRER_POLICY = 'same-origin'` y `SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'`.
- [ ] `config/settings.py` — Evaluar/reemplazar `SECURE_BROWSER_XSS_FILTER` (deprecado en Django 5.x).
- [ ] Test: request con `HTTP_X_FORWARDED_PROTO=https` → `request.is_secure()` True y cookie secure set.

## Registro de tareas Huey

- [ ] `apps/core/apps.py` — Importar `from apps.core import tasks` (u otro mecanismo) en `ready()`.
- [ ] Revisar otras apps con tareas (commercial, meteo, user_auth) e importarlas igualmente.
- [ ] Verificar: `huey_consumer config.huey.huey` registra las tareas (log de arranque o inspección).
- [ ] (Alternativa si ready() falla) Importar tasks en `config/huey.py`.

## Fail-closed sin `.env`

- [ ] `config/settings.py` — Agregar guard: si `IS_PRODUCTION` (o `DEBUG` explícitamente False) y faltan `SECRET_KEY`/`DB_*`, lanzar `ImproperlyConfigured` con mensaje claro.
- [ ] `config/settings.py:21` — `DEBUG` default → `False` (o `os.getenv('DEBUG', 'False')`), nunca `'True'`.
- [ ] Mantener `get_random_secret_key()` solo para dev.
- [ ] Test: sin `.env` con `PRODUCTION=true` → `ImproperlyConfigured`.

## Gunicorn sin root

- [ ] `gunicorn.sh` — Ejecutar como el usuario del sistema que posee el venv (no root); quitar `USER=root/GROUP=root`.
- [ ] `README.md` — Actualizar ejemplo de Supervisor con el usuario correcto.
- [ ] `README.md` — Documentar mejora futura: usuario dedicado `webcmp` + chown (roadmap backlog).

## Verificación

- [ ] `python manage.py check`
- [ ] `python manage.py test`
- [ ] Actualizar roadmap.md (mover 089 a Hecho al completar).
- [ ] Commit.
