"""Perfil `production`: `PRODUCTION` presente en el entorno.

Lo elige el dispatcher solo si `PRODUCTION` está en `os.environ`. La exporta
`Environment=PRODUCTION=1` en `deploy/systemd/webcmp.service`, y no hay otro
lugar del que sale: por eso el perfil de producción NO se puede alcanzar por
otra vía, y no depende de `DEBUG` para ninguna de sus decisiones.
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

# `DEBUG` pineado y NO heredado de `base` (que lo lee de `.env`): un `DEBUG=True`
# colado en el `.env` de producción publicaría tracebacks con paths del servidor a
# cualquiera que alcance un 500. El costo es una línea más de diff en el estado
# híbrido `PRODUCTION=1 DEBUG=True`, que es exactamente el que este perfil evita.
DEBUG = False

# La falta de SECRET_KEY ya no se comprueba acá: `base.load_secret_key()` falla
# cerrado para TODOS los perfiles, con un mensaje que nombra el archivo y el comando
# exacto. Dos dueños para la misma regla es una regla que alguien va a parchear en
# uno de los dos. Lo que SÍ es propio de producción y no se puede expresar en
# `base` es el correo por consola, de abajo.

# Anti-consola. El pie real no es "dev usa consola", es "producción usa consola en
# silencio": los correos se descartan en stdout y ni el operador ni el usuario se
# enteran. Se compara el PATH y no se resuelve la clase porque este módulo se
# importa desde `django.setup()`, antes de que exista una app configurada donde
# importar `EMAIL_BACKEND`. Solo se rechaza el de consola: cualquier otro backend
# pasa, incluido `config.custom_email_backend.CustomSTARTTLSBackend`, que es real.
if EMAIL_BACKEND.strip() == console_email_backend:
    raise ImproperlyConfigured(
        'Producción no puede enviar correo por consola: EMAIL_BACKEND apunta a '
        f'{console_email_backend} y los mensajes se perderían en silencio. Defina un '
        'servidor SMTP real (EMAIL_BACKEND, EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, '
        'EMAIL_HOST_PASSWORD) y regenere el archivo con '
        '`python scripts/generate_env.py --production`.'
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
