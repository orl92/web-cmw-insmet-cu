"""Perfil `production`: `PRODUCTION` presente en el entorno.

Lo elige el dispatcher solo si `PRODUCTION` está en `os.environ`. `gunicorn.sh`
no exporta esa variable (la define el `supervisord.conf` del servidor de deploy,
fuera del repo): por eso el perfil de producción NO se puede alcanzar por otra
vía, y no depende de `DEBUG` para ninguna de sus decisiones.
"""

# Los settings de `base` llegan por `import *` a propósito: un perfil tiene que
# ser un módulo de settings completo por sí solo, no un parche del dispatcher.
# ruff: noqa: F405
import os

from .base import *  # noqa: F403
from .base import (  # noqa: F401  (alias sin guion bajo: `import *` no lo exporta)
    _CONTENT_SECURITY_POLICY_DIRECTIVES,
    apply_external_hostname,
    decrypt_secret_key,
    resolve_obs_local_only,
)

# Sin DEBUG en el entorno, `SECRET_KEY` de `base` es una clave temporal por
# sesión. Producción falla cerrado. El orden importa: este raise venía antes que
# el de la base de datos en el monolito y debe seguir siendo el primero.
if decrypt_secret_key(os.getenv('SECRET_KEY'), os.getenv('ENCRYPTION_KEY')) is None:
    raise ImproperlyConfigured(
        'SECRET_KEY y ENCRYPTION_KEY no están definidas. '
        'Ejecute `python manage.py generate_env` (o `--production`) '
        'para generar el archivo .env.'
    )

# Security
SECURE_SSL_REDIRECT = False  # Nginx termina TLS y redirige a HTTPS; Django no lo hace.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Sin debug toolbar: el flag se lee en `config/urls.py` y en las apps, así que
# existe siempre; aquí vale False.
DEBUG_TOOLBAR_ENABLED = False

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    # WhiteNoise con manifest hasheado exige collectstatic previo.
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

if whitenoise_middleware not in MIDDLEWARE:
    MIDDLEWARE = [*MIDDLEWARE[:1], whitenoise_middleware, *MIDDLEWARE[1:]]

# `is_production=True` activa el fail-closed sin DB_ENGINE; `prefer_sqlite=False`
# porque producción no acepta el atajo a sqlite que hoy daría un `DEBUG=True`
# colado en el entorno (el `if DEBUG or ...` del monolito).
DATABASES = get_database_config(is_production=True, prefer_sqlite=False)

if external_hostname := os.getenv('EXTERNAL_HOSTNAME', ''):
    apply_external_hostname(external_hostname, ['http://', 'https://'])

OBS_LOCAL_ONLY_DEFAULT = False
OBS_LOCAL_ONLY = resolve_obs_local_only(OBS_LOCAL_ONLY_DEFAULT)
