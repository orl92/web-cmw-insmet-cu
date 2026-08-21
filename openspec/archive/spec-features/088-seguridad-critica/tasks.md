# Tasks — 088-seguridad-critica

## FTP credentials

- [x] `config/settings.py` — Agregar `FTP_OBS_HOST = os.getenv('FTP_OBS_HOST')`, `FTP_OBS_USER`, `FTP_OBS_PASS` (sin valores por defecto en producción).
- [x] `apps/api/data/FileObs.py` — Aceptar credenciales por constructor (`__init__(self, host=None, user=None, password=None)`) leyendo de settings como fallback; eliminar los literales `HOST/USER/PASS`.
- [x] `apps/api/views.py` (StationObservationView y cualquier otro que instancie FileObs) — pasar credenciales desde settings.
- [x] `apps/core/management/commands/generate_env.py` — Escribir `FTP_OBS_HOST/USER/PASS` en `.env` con valores de ejemplo.
- [x] `env.sample` — Agregar `FTP_OBS_HOST`, `FTP_OBS_USER`, `FTP_OBS_PASS`.
- [x] `.secrets.baseline` — Re-escanear y actualizar si `detect-secrets` detecta algo nuevo.
- [x] `SECURITY.md` o README — Documentar **rotación manual de la password FTP** (quedó expuesta en git history; cambiarla en el servidor al tener acceso).
- [x] Verificar: `grep -rn "CasaB2024\|10.0.100.224" apps/ config/` → sin resultados en código.

## Rate limiting

- [x] `config/settings.py` — Agregar `'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.AnonRateThrottle', 'rest_framework.throttling.UserRateThrottle']` en `REST_FRAMEWORK`.
- [x] Verificar que `DEFAULT_THROTTLE_RATES` sigue con anon 100/h, user 1000/h.
- [x] Test: request anónimo >100 a `/api/stations/` → 429.

## Auth endpoints

- [x] `apps/meteo/views/forecast.py` (ExcelJSONView) — Agregar `LoginRequiredMixin` + `PermissionRequiredMixin` (permiso `meteo.change_forecast`); evaluar y documentar el `csrf_exempt` (remover si el cliente JS no lo requiere).
- [x] Verificar el JS/cliente que consume ExcelJSONView y ajustar si se quita csrf_exempt.
- [x] `apps/commercial/views/invoices.py` (ajax_pending_subscriptions) — Agregar `@login_required` + `@permission_required('commercial.view_servicesubscription')`; filtrar por ownership (cliente propio) salvo staff/superuser.
- [x] Proxys de imagen/GIF (`apps/home/views/modelos/views.py`, `apps/home/views/satelites/views.py`) — Agregar `django-ratelimit` con límite por IP (ej. 300/h), o throttle manual si no se quiere nueva dependencia.
- [x] `DescargarGifView` — Limitar descargas por request (ya baja 25; documentar o reducir).

## ASGI + open redirect + email backend

- [x] `config/asgi.py:14` — `'config .settings'` → `'config.settings'`.
- [x] `apps/user_auth/views/login.py` — Validar `next`: solo rutas relativas sin `//` ni `://`; agregar helper/test.
- [x] **Mantener** `config/custom_email_backend.py` (`CustomSTARTTLSBackend`): el correo del proyecto usa certificado autofirmado → requiere desactivar verificación TLS. No es dead code: `settings.py` lee `EMAIL_BACKEND` desde env.
- [x] `apps/core/management/commands/generate_env.py` — Escribe `EMAIL_BACKEND` apuntando al backend custom cuando el correo es autofirmado (modo interactivo pregunta; `--production` lo usa por defecto).
- [x] `config/settings.py` — Confirmar `EMAIL_USE_TLS=True` en el backend SMTP.
- [x] `apps/core/management/commands/generate_env.py` — **Modo interactivo**: pregunta prod/dev, luego va variable por variable mostrando el default y permitiendo sobreescribir; para passwords/correos permite ingresar el valor real (getpass). FTP, email y **BD incluidos**.
- [x] `generate_env.py` — **Menú de motor de BD**: dev → `sqlite3 | postgresql | mysql`; prod → `postgresql | mysql`. SQLite en dev escribe `DB_ENGINE=sqlite3` + `DB_NAME=db.sqlite3` (corrige bug de SQLite en memoria que tenía el bloque dev previo).
- [x] `generate_env.py` — **Regeneración**: si `.env` existe, se regenera usando los valores actuales como defaults (Enter = mantener). `SECRET_KEY`/`ENCRYPTION_KEY` se **conservan por defecto** (no invalidar sesiones); se **rotan** si el usuario confirma en modo interactivo o con `--rotate-keys` (caso de clave comprometida). Si falta alguna clave se generan nuevas con aviso.

## Verificación

- [x] `python manage.py check`
- [x] `python manage.py test apps.api apps.meteo apps.commercial apps.user_auth apps.core`
- [x] `python manage.py generate_env --development` y modo interactivo (smoke test) generan .env con `EMAIL_BACKEND` correcto y FTP.
- [x] Actualizar roadmap.md (mover 088 a Hecho al completar).
- [x] Commit.
