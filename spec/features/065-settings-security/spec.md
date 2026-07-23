# 065 — settings-security

## Motivación

La configuración de seguridad está bien encaminada (SECRET_KEY encriptado,
DEBUG por entorno, ALLOWED_HOSTS dinámico) pero falta un componente crítico
para una app con API REST: **CORS**. El proyecto expone endpoints en
`/api/` (DRF) pero no hay `django-cors-headers` instalado ni configurado.
Esto significa que cualquier frontend en otro origen no podrá consumir la
API. Adicionalmente, la rate limiting solo cubre anon/user pero no hay
límites específicos por endpoint sensible.

## Alcance

- `config/settings.py`
- `requirements.txt`
- `apps/api/` (vistas, throttles)

## Criterios de Aceptación

1. `django-cors-headers` está en requirements.txt e instalado.
2. `corsheaders` está en INSTALLED_APPS.
3. `CorsMiddleware` está en MIDDLEWARE (alto, antes de CommonMiddleware).
4. `CORS_ALLOWED_ORIGINS` se lee desde variable de entorno.
5. `CORS_ALLOW_CREDENTIALS = True` solo si es necesario.
6. Endpoints de API responden con headers CORS correctos.
7. Tests existentes siguen pasando.
