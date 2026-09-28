"""Perfil `dev`: desarrollo local con `DEBUG=True`.

Se elige cuando `DEBUG=True` y `PRODUCTION` NO está en el entorno (ver el
dispatcher `config/settings/__init__.py`). Un archivo de perfil no ramifica sobre
el entorno: cada ajuste de este perfil es una decisión fija, y la variable de
entorno que lo selecciona es la única que lee el dispatcher.
"""

# Los settings de `base` llegan por `import *` a propósito: un perfil tiene que
# ser un módulo de settings completo por sí solo, no un parche del dispatcher.
# ruff: noqa: F405
import logging
import os

from .base import *  # noqa: F403
from .base import (  # noqa: F401  (alias sin guion bajo: `import *` no lo exporta)
    _CONTENT_SECURITY_POLICY_DIRECTIVES,
    apply_external_hostname,
    resolve_obs_local_only,
)

DEBUG = True

# Security: sin bloque de cookies seguras (el servidor local no termina TLS).
# En el monolito era `if not DEBUG:`; aquí lo decide el perfil.

# Django 5.1+ usa STORAGES (STATICFILES_STORAGE quedó obsoleto y no tiene
# efecto). Sin manifest hasheado: `collectstatic` es opcional en dev.
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

DEBUG_TOOLBAR_ENABLED = True
INTERNAL_IPS = ['127.0.0.1', '::1']
DEBUG_TOOLBAR_CONFIG = {'IS_RUNNING_TESTS': False}

INSTALLED_APPS = [*INSTALLED_APPS, 'debug_toolbar']
MIDDLEWARE = [mw for mw in MIDDLEWARE if mw != whitenoise_middleware] + [
    'debug_toolbar.middleware.DebugToolbarMiddleware'
]

# `prefer_sqlite=True`: sqlite gana aunque `.env` traiga DB_ENGINE. En el
# monolito lo garantizaba el `DEBUG` del propio módulo; aquí lo impone el perfil
# DESPUÉS de su `import *`.
DATABASES = get_database_config(is_production=IS_PRODUCTION, prefer_sqlite=True)

if external_hostname := os.getenv('EXTERNAL_HOSTNAME', ''):
    apply_external_hostname(external_hostname, ['http://'])

OBS_LOCAL_ONLY_DEFAULT = True
OBS_LOCAL_ONLY = resolve_obs_local_only(OBS_LOCAL_ONLY_DEFAULT)

if os.getenv('LDAP_SERVER_URI'):
    logging.getLogger('ldap3_auth').setLevel(logging.DEBUG)
