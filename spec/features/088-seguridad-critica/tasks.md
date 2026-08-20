# Tasks — 088-seguridad-critica

## FTP credentials

- [ ] `config/settings.py` — Agregar `FTP_OBS_HOST = os.getenv('FTP_OBS_HOST')`, `FTP_OBS_USER`, `FTP_OBS_PASS` (sin valores por defecto en producción).
- [ ] `apps/api/data/FileObs.py` — Aceptar credenciales por constructor (`__init__(self, host=None, user=None, password=None)`) leyendo de settings como fallback; eliminar los literales `HOST/USER/PASS`.
- [ ] `apps/api/views.py` (StationObservationView y cualquier otro que instancie FileObs) — pasar credenciales desde settings.
- [ ] `apps/core/management/commands/generate_env.py` — Escribir `FTP_OBS_HOST/USER/PASS` en `.env` con valores de ejemplo.
- [ ] `env.sample` — Agregar `FTP_OBS_HOST`, `FTP_OBS_USER`, `FTP_OBS_PASS`.
- [ ] `.secrets.baseline` — Re-escanear y actualizar si `detect-secrets` detecta algo nuevo.
- [ ] `SECURITY.md` o README — Documentar **rotación manual de la password FTP** (quedó expuesta en git history; cambiarla en el servidor al tener acceso).
- [ ] Verificar: `grep -rn "CasaB2024\|10.0.100.224" apps/ config/` → sin resultados en código.

## Rate limiting

- [ ] `config/settings.py` — Agregar `'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.AnonRateThrottle', 'rest_framework.throttling.UserRateThrottle']` en `REST_FRAMEWORK`.
- [ ] Verificar que `DEFAULT_THROTTLE_RATES` sigue con anon 100/h, user 1000/h.
- [ ] Test: request anónimo >100 a `/api/stations/` → 429.

## Auth endpoints

- [ ] `apps/meteo/views/forecast.py` (ExcelJSONView) — Agregar `LoginRequiredMixin` + `PermissionRequiredMixin` (permiso `meteo.change_forecast`); evaluar y documentar el `csrf_exempt` (remover si el cliente JS no lo requiere).
- [ ] Verificar el JS/cliente que consume ExcelJSONView y ajustar si se quita csrf_exempt.
- [ ] `apps/commercial/views/invoices.py` (ajax_pending_subscriptions) — Agregar `@login_required` + `@permission_required('commercial.view_servicesubscription')`; filtrar por ownership (cliente propio) salvo staff/superuser.
- [ ] Proxys de imagen/GIF (`apps/home/views/modelos/views.py`, `apps/home/views/satelites/views.py`) — Agregar `django-ratelimit` con límite por IP (ej. 300/h), o throttle manual si no se quiere nueva dependencia.
- [ ] `DescargarGifView` — Limitar descargas por request (ya baja 25; documentar o reducir).

## ASGI + open redirect + email backend

- [ ] `config/asgi.py:14` — `'config .settings'` → `'config.settings'`.
- [ ] `apps/user_auth/views/login.py` — Validar `next`: solo rutas relativas sin `//` ni `://`; agregar helper/test.
- [ ] Eliminar `config/custom_email_backend.py`.
- [ ] `apps/core/management/commands/generate_env.py` — Quitar `CUSTOM_EMAIL_BACKEND` y `EMAIL_USE_SSL` si ya no aplican.
- [ ] `config/settings.py` — Confirmar `EMAIL_USE_TLS=True` en el backend SMTP.

## Verificación

- [ ] `python manage.py check`
- [ ] `python manage.py test apps.api apps.meteo apps.commercial apps.user_auth apps.core`
- [ ] Actualizar roadmap.md (mover 088 a Hecho al completar).
- [ ] Commit.
