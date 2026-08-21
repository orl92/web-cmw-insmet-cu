# Tasks — 065-settings-security

## Dependencia

- [ ] `requirements.txt` — Agregar `django-cors-headers`

## Settings

- [ ] `config/settings.py:207-224` — Agregar `'corsheaders'` a INSTALLED_APPS
- [ ] `config/settings.py:226-237` — Agregar
      `'corsheaders.middleware.CorsMiddleware'` al inicio de MIDDLEWARE
      (antes de `CommonMiddleware`)
- [ ] Configurar `CORS_ALLOWED_ORIGINS` desde
      `os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')`
- [ ] Configurar `CORS_ALLOW_CREDENTIALS = True`
- [ ] Configurar `CORS_URLS_REGEX = r'^/api/.*'`

## Variables de entorno

- [ ] `env.sample` — Agregar `CORS_ALLOWED_ORIGINS` con valor por defecto
      `http://localhost:8000,http://127.0.0.1:8000`

## Verificación

- [ ] `pip install -r requirements.txt` (instalar django-cors-headers)
- [ ] `python manage.py check`
- [ ] `python manage.py test`
- [ ] Hacer request OPTIONS a `/api/stations/` y verificar header
      `Access-Control-Allow-Origin`

## Fase 2 — Rate limiting real (ver 088-seguridad-critica)

- [ ] `config/settings.py` — Agregar `DEFAULT_THROTTLE_CLASSES` en `REST_FRAMEWORK` (hoy solo hay `DEFAULT_THROTTLE_RATES`, sin clases → el limit no aplica)
- [ ] Test: anon >100/h a `/api/stations/` → 429
- [ ] Throttle por IP en proxys de imagen/GIF públicos (django-ratelimit o manual)
