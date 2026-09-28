"""Perfil `testing`: sin `DEBUG` y sin `PRODUCTION`.

Es el estado de CI, pero también el de un `manage.py test` local o de un staging
mal configurado, por eso no se llama `ci`. Lo elige el dispatcher cuando
`PRODUCTION` no está en el entorno y `DEBUG` no es `True`.
"""

# Los settings de `base` llegan por `import *` a propósito: un perfil tiene que
# ser un módulo de settings completo por sí solo, no un parche del dispatcher.
# ruff: noqa: F405
import os

from .base import *  # noqa: F403
from .base import (  # noqa: F401  (alias sin guion bajo: `import *` no lo exporta)
    _CONTENT_SECURITY_POLICY_DIRECTIVES,
    apply_external_hostname,
    resolve_obs_local_only,
)

DEBUG = False

# Security
# El bloque era `if not DEBUG:` en el monolito; acá es la definición del perfil.
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
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

MIDDLEWARE = [mw for mw in MIDDLEWARE if mw != whitenoise_middleware]

# `prefer_sqlite=False` con la lógica real de `get_database_config()`: sqlite
# salvo que `.env` defina DB_ENGINE. Es lo que hacía el monolito con
# DEBUG=False e IS_PRODUCTION=False.
DATABASES = get_database_config(is_production=IS_PRODUCTION, prefer_sqlite=False)

if external_hostname := os.getenv('EXTERNAL_HOSTNAME', ''):
    apply_external_hostname(external_hostname, ['http://', 'https://'])

OBS_LOCAL_ONLY_DEFAULT = False
OBS_LOCAL_ONLY = resolve_obs_local_only(OBS_LOCAL_ONLY_DEFAULT)
