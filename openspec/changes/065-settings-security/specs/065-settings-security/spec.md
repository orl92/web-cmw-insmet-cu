# Spec — 065-settings-security

## Criterios de Aceptación

1. `django-cors-headers` está en requirements.txt e instalado.
2. `corsheaders` está en INSTALLED_APPS.
3. `CorsMiddleware` está en MIDDLEWARE (alto, antes de CommonMiddleware).
4. `CORS_ALLOWED_ORIGINS` se lee desde variable de entorno.
5. `CORS_ALLOW_CREDENTIALS = True` solo si es necesario.
6. Endpoints de API responden con headers CORS correctos.
7. Tests existentes siguen pasando.
