# Plan — 065-settings-security

## Estrategia

1. Agregar `django-cors-headers` a `requirements.txt`.
2. Agregar `'corsheaders'` a `INSTALLED_APPS`.
3. Agregar `'corsheaders.middleware.CorsMiddleware'` al inicio de MIDDLEWARE
   (justo después de SecurityMiddleware, antes de CommonMiddleware).
4. Leer `CORS_ALLOWED_ORIGINS` desde `.env` con split por coma, similar a
   `ALLOWED_HOSTS`.
5. Configurar `CORS_ALLOW_CREDENTIALS = True` si se usan cookies/sesiones
   desde el frontend (probablemente sí, porque la API usa session auth).
6. Mantener `CORS_URLS_REGEX = r'^/api/.*'` para solo habilitar en API.

## Orden recomendado

1. Agregar dependencia
2. Configurar settings
3. Agregar variable al env.sample
4. Probar con un request OPTIONS a un endpoint API

## Riesgos

- `CorsMiddleware` debe ir **antes** que `CommonMiddleware` o no funcionará
  correctamente. Orden correcto en MIDDLEWARE.
- Si se habilita `CORS_ALLOW_ALL_ORIGINS = True` por error en producción,
  es un riesgo de seguridad. Usar lista explícita desde .env.
- La variable `CORS_ALLOWED_ORIGINS` debe agregarse a `env.sample` y
  documentarse.
