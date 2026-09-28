"""Configuración compartida por los tres perfiles de `config.settings`.

Contiene lo que NO depende del perfil: `.env`, plantillas, apps, DRF, i18n,
estáticos, correo, LDAP, FTP, CSP y logging. Las decisiones de entorno (cookies
seguras, STORAGES, debug toolbar, WhiteNoise y base de datos) viven en `dev.py`,
`testing.py` y `production.py`.

REGLA ESTRUCTURAL (no negociable): este módulo NO ramifica sobre `DEBUG` ni
sobre `IS_PRODUCTION`, solo los lee como valores planos. Cada perfil hace
`from .base import *`, que ejecuta este archivo ANTES de que el perfil pueda
corregir nada: si aquí se calculara `DATABASES` con el `DEBUG` de `base`, el
perfil ya no podría imponer el suyo. Ver odd/tasks/split-config-settings.md.
"""

import logging
import os
import warnings
from pathlib import Path

from cryptography.fernet import Fernet
from django.contrib.messages import constants as messages
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from django.urls import reverse_lazy
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / '.env')

# Las dos banderas que el dispatcher de `config/settings/__init__.py` usa para
# elegir perfil. Son las MISMAS lecturas que hacía el monolito: perfil de
# producción inalcanzable sin `PRODUCTION` en el entorno.
IS_PRODUCTION = 'PRODUCTION' in os.environ

DEBUG = os.getenv('DEBUG', 'False') == 'True'

# ---------------------------------------------------------------------------
# Cache backend
# By default the app uses Django's in-process LocMemCache so dev/CI run with no
# Redis server. When USE_REDIS_CACHE=True the shared RedisCache backend is used
# (LOCATION driven by REDIS_URL). The native Django >= 4.0 Redis backend only
# requires the `redis` (redis-py) package -- no django-redis dependency.
# ---------------------------------------------------------------------------
USE_REDIS_CACHE = os.getenv('USE_REDIS_CACHE', 'False') == 'True'

REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')


def build_caches(use_redis, redis_url):
    """Construye el dict CACHES de forma determinista y testeable.

    Por defecto usa LocMemCache (sin servidor Redis, para dev/CI). Cuando
    *use_redis* es True se selecciona el backend RedisCache nativo de Django
    (>= 4.0); su conexión es perezosa, por lo que no requiere un Redis activo
    hasta que el cache se usa realmente.
    """
    caches = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        },
    }
    if use_redis:
        caches['default'] = {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': redis_url,
        }
    return caches


CACHES = build_caches(USE_REDIS_CACHE, REDIS_URL)


def decrypt_secret_key(encrypted_secret_key, encryption_key):
    if not encrypted_secret_key or not encryption_key:
        return None

    cipher_suite = Fernet(encryption_key.encode())
    return cipher_suite.decrypt(encrypted_secret_key.encode()).decode()


SECRET_KEY = decrypt_secret_key(
    os.getenv('SECRET_KEY'),
    os.getenv('ENCRYPTION_KEY'),
)


class EphemeralSecretKeyWarning(UserWarning):
    """Categoría propia para el fallback a `get_random_secret_key()`.

    No es un `UserWarning` pelado a propósito: con categoría propia el aviso es
    grepeable y un operador puede endurecerlo después con
    `-W error::config.settings.base.EphemeralSecretKeyWarning` sin tocar código.
    """


if SECRET_KEY is None:
    # Sin .env cifrado: clave temporal por sesión. NO se puede fallar cerrado acá.
    # `generate_env` es un management command, y `manage.py` importa los settings
    # ANTES de despacharlo (`django.setup()`): un raise en este bloque dejaría sin
    # arranque al propio comando que existe para generar la clave (paradoja de
    # bootstrap; ver odd/tasks/harden-settings-profiles-deploy-gate.md).
    # El fallback ES el bypass de bootstrap; el defecto nunca fue el fallback sino
    # que fuera silencioso. Por eso ahora avisa. En producción `production.py`
    # convierte este bloque en un fail-fast de verdad.
    SECRET_KEY = get_random_secret_key()
    warnings.warn(
        'SECRET_KEY ausente o no descifrable con ENCRYPTION_KEY: se está usando una clave '
        'efímera que cambia en cada reinicio del proceso, así que todas las sesiones y '
        'cookies firmadas quedan invalidadas. Ejecute `python manage.py generate_env` para '
        'escribir un .env con SECRET_KEY y ENCRYPTION_KEY válidas. El perfil de producción '
        '(PRODUCTION=1) falla cerrado ante esto; este aviso corresponde a dev o CI sin .env.',
        EphemeralSecretKeyWarning,
        # `stacklevel=1` y no 2: el aviso tiene que señalar el punto donde se acuña
        # la clave efímera (este `warnings.warn`). Con 2 apuntaría al `from .base
        # import *` del perfil o del dispatcher, que no es donde está la causa.
        stacklevel=1,
    )

# ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS
ALLOWED_HOSTS = [
    h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()
]
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(
        ','
    )
    if o.strip()
]


def apply_external_hostname(external_hostname, schemes):
    """Agrega el dominio de EXTERNAL_HOSTNAME a ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS.

    *schemes* es la decisión del perfil: solo `http://` en dev (el servidor local
    no termina TLS) y `http://` + `https://` en testing y producción. El bloque
    queda en una función porque el `import *` del perfil corre antes de que este
    perfil pueda fijar sus esquemas.
    """
    domain = (
        external_hostname.replace('https://', '').replace('http://', '').split('/')[0].split(':')[0]
    )
    if domain not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(domain)
    for scheme in schemes:
        origin = f'{scheme}{domain}'
        if ':' in external_hostname.split('://')[-1]:
            origin += f':{external_hostname.split(":")[-1]}'
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)


# Application
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'csp',
    'drf_redesign',
    'rest_framework',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'apps.api.apps.ApiConfig',
    'apps.home.apps.HomeConfig',
    'apps.publications.apps.PublicationsConfig',
    'apps.core.apps.CoreConfig',
    'apps.user_auth.apps.UserAuthConfig',
    'apps.meteo.apps.MeteoConfig',
    'apps.commercial.apps.CommercialConfig',
    'apps.dashboard.apps.DashboardConfig',
]

# La lista base incluye WhiteNoise y el debug toolbar NO: cada perfil decide
# si lo deja, si lo quita y si añade el toolbar. Los perfiles que modifiquen
# estas listas deben COPIARLAS primero (`[*LIST, ...]`): `base` es un módulo
# compartido, y una mutación in place (`.append`, `+=`, `.remove`) contaminaría
# a los otros perfiles importados en el mismo proceso (p. ej. los tests que
# cargan los tres para comparar la tabla de verdad).
# En minúscula a propósito: un nombre en MAYÚSCULAS en un módulo de settings es
# un setting, y Django copiaría la constante al objeto `settings`.
whitenoise_middleware = 'whitenoise.middleware.WhiteNoiseMiddleware'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    whitenoise_middleware,
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'csp.middleware.CSPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.CheckUserProfileMiddleware',
    'apps.core.middleware.MaintenanceModeMiddleware',
]

# ---------------------------------------------------------------------------
# Content Security Policy (CSP) — django-csp
# ---------------------------------------------------------------------------
# The policy restricts resource origins to 'self' while allowing documented
# exceptions for inline scripts/styles (interim, nonce refactor pending) and
# external weather-symbol images from cdn.jsdelivr.net.
# See openspec/changes/archive/2026-08-28-011-csp/design.md for full rationale.
#
# NOTE (deviation from design draft): django-csp 4.x uses the
# `CONTENT_SECURITY_POLICY` dict with a `DIRECTIVES` sub-dict and the middleware
# class `csp.middleware.CSPMiddleware` (the 3.x `ContentSecurityPolicyMiddleware`
# class and flat dict were renamed/restructured in the 4.0 migration).
_CONTENT_SECURITY_POLICY_DIRECTIVES = {
    'default-src': ["'self'"],
    'base-uri': ["'self'"],
    'frame-ancestors': ["'self'"],
    # 'self' (formerly 'none'): the dashboard PDF modal renders documents in an
    # <object type="application/pdf"> (templates/includes/home/document_pdf_modal.html).
    # object-src 'none' blocked that object, so the modal only showed the
    # download fallback. 'self' allows embedding same-origin PDFs while still
    # blocking data:/external object sources.
    'object-src': ["'self'"],
    # 'unsafe-inline' required: 41 inline <script> blocks
    # (e.g. templates/includes/base/scripts.html:8,
    #  templates/includes/dashboard/footer.html:41).
    # Nonce migration is a tracked follow-up.
    'script-src': ["'self'", "'unsafe-inline'"],
    # 'unsafe-inline' required: inline <style> blocks
    # (e.g. templates/includes/base/head.html:15).
    'style-src': ["'self'", "'unsafe-inline'"],
    # jsdelivr required for meteogram.js:128,255 weather-symbol SVGs.
    'img-src': ["'self'", 'data:', 'https://cdn.jsdelivr.net'],
    'font-src': ["'self'"],
    'connect-src': ["'self'"],
}

CONTENT_SECURITY_POLICY = {'DIRECTIVES': _CONTENT_SECURITY_POLICY_DIRECTIVES}

# CSP_REPORT_ONLY (env var, project os.getenv helper — no environs dependency):
# when 'True' the middleware emits Content-Security-Policy-Report-Only INSTEAD of
# the enforced header, so staging can observe violations without enforcement.
# Default False = enforced policy in production.
# NOTE: django-csp 4.0 removed the `CSP_REPORT_ONLY` settings flag (it now emits
# a csp.E001 system-check error); the env toggle drives the 4.0
# CONTENT_SECURITY_POLICY_REPORT_ONLY dict instead.
# La exclusión es mutua: existe CONTENT_SECURITY_POLICY o
# CONTENT_SECURITY_POLICY_REPORT_ONLY, nunca los dos.
if os.getenv('CSP_REPORT_ONLY', 'False') == 'True':
    CONTENT_SECURITY_POLICY = None
    CONTENT_SECURITY_POLICY_REPORT_ONLY = {
        'DIRECTIVES': _CONTENT_SECURITY_POLICY_DIRECTIVES,
    }

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

HOME_TEMPLATES = BASE_DIR / 'templates'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [HOME_TEMPLATES],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.menu_notifications',
                'apps.core.context_processors.site_branding',
            ],
        },
    },
]


# Database
def get_database_config(*, is_production=IS_PRODUCTION, prefer_sqlite=DEBUG):
    """Construye el dict DATABASES a partir de las variables de entorno.

    Los dos bandos se reciben como argumentos, con los valores de `base` por
    defecto, porque cada perfil los impone DESPUÉS de su `import *`: quien llama
    tiene que poder decir "mi perfil no prefiere sqlite" o "mi perfil no es
    producción" sin que `base` se adelante.

    - *is_production* activa el fail-closed sin `DB_ENGINE` (solo producción).
    - *prefer_sqlite* hace que sqlite gane aunque `DB_ENGINE` esté definida
      (equivalente al antiguo `if DEBUG or ...`, que solo dev lo pedía).
    """
    db_engine = os.getenv('DB_ENGINE', '').strip().lower()

    if is_production and not db_engine:
        raise ImproperlyConfigured(
            'Falta la configuración de la base de datos. Defina DB_ENGINE (y DB_NAME, '
            'DB_USER, DB_HOST, DB_PASS) en el archivo .env. '
            'Ejecute `python manage.py generate_env --production` para generarlo.'
        )

    # sqlite3 NO usa usuario, password ni host. La decisión va ANTES del chequeo de
    # credenciales, no después: si el motor ya es sqlite, exigir DB_USER/DB_HOST/
    # DB_PASS obligaría a inventar cuatro valores que el motor nunca lee, y un
    # `.env` con `DB_ENGINE=sqlite3` (dev con DEBUG=False, staging, el gate de CI)
    # no podría arrancar ningún perfil. Antes de este corte, el perfil `testing`
    # fallaba con un mensaje que además decía "Para producción" sin serlo.
    if prefer_sqlite or db_engine in {'', 'sqlite', 'sqlite3'}:
        return {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }

    if not all(os.getenv(k) for k in ('DB_NAME', 'DB_USER', 'DB_HOST', 'DB_PASS')):
        raise ImproperlyConfigured(
            f'El motor "{db_engine}" necesita DB_NAME, DB_USER, DB_HOST y DB_PASS, y al menos '
            'uno falta o está vacío en el entorno. (sqlite3 no los necesita: para él, alcanzaba '
            'con DB_ENGINE=sqlite3.) Defina las cuatro en el archivo .env.'
        )

    db_config = {
        'ENGINE': f'django.db.backends.{db_engine}',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASS'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432' if db_engine == 'postgresql' else '3306'),
        'CONN_MAX_AGE': 600,
    }

    ssl_mode = os.getenv('DB_SSL_MODE', 'prefer' if db_engine == 'postgresql' else 'PREFERRED')
    db_config['OPTIONS'] = {}

    if db_engine == 'postgresql':
        db_config['OPTIONS']['sslmode'] = ssl_mode
        if ssl_mode in ('verify-ca', 'verify-full') and (cert := os.getenv('DB_SSL_ROOT_CERT')):
            db_config['OPTIONS']['sslrootcert'] = cert

    elif db_engine == 'mysql':
        db_config['OPTIONS']['ssl_mode'] = ssl_mode.upper()
        if ssl_mode.upper() in ('VERIFY_CA', 'VERIFY_IDENTITY'):
            for k in ('ca', 'cert', 'key'):
                if v := os.getenv(f'DB_SSL_{k.upper()}'):
                    db_config['OPTIONS'].setdefault('ssl', {})[k] = v

    return {'default': db_config}


# El que arma DATABASES es el perfil (ver la nota de `get_database_config`), no
# este módulo.

# Auth
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_REDIRECT_URL = reverse_lazy('home:index')
LOGOUT_REDIRECT_URL = reverse_lazy('home:index')
LOGIN_URL = reverse_lazy('user_auth:login')

GROUP_PERMISSION_EXCLUDED_APPS = [
    'auth',
    'user_auth',
    'admin',
    'contenttypes',
    'sessions',
    'messages',
    'staticfiles',
]
GROUP_PERMISSION_APP_MERGE = {
    'auth': 'user_auth',
}
GROUP_PERMISSION_MODEL_MERGE = {
    'Pronóstico': 'Pronóstico',
    'Pronóstico por Región': 'Pronóstico',
    'Día Extendido': 'Pronóstico',
    'Factura': 'Facturacion',
    'Item': 'Facturacion',
    'Correo': 'Lista de correo',
}

MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Internationalization
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Havana'
USE_I18N = True
USE_TZ = True

TIME_INPUT_FORMATS = ['%H:%M:%S', '%H:%M:%S.%f', '%H:%M', '%I:%M %p', '%I:%M %P']
DATETIME_INPUT_FORMATS = [
    '%d/%m/%Y %H:%M:%S',
    '%d/%m/%Y %H:%M:%S.%f',
    '%d/%m/%Y %H:%M',
    '%d/%m/%y %H:%M:%S',
    '%d/%m/%y %H:%M:%S.%f',
    '%d/%m/%y %H:%M',
    '%d/%m/%Y %I:%M %p',
    '%d/%m/%y %I:%M %p',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M:%S.%f',
    '%Y-%m-%d %H:%M',
    '%Y-%m-%d',
]

# Static files
# STORAGES lo fija cada perfil: WhiteNoise con manifest hasheado en producción
# (Django 5.1+ usa STORAGES; STATICFILES_STORAGE quedó obsoleto y no tiene
# efecto) y el backend estático simple en dev/testing.
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# media/ is created at startup via apps.core.apps.CoreConfig.ready()
# (idempotent exist_ok mkdir). No manual step required.

# Los tests escriben en un MEDIA_ROOT temporal que se autolimpia (evita
# dejar archivos residuales en media/).
TEST_RUNNER = 'config.test_runner.IsolatedMediaRunner'

# Clickjacking protection: DENY (no first-party view is embedded in a frame;
# change 013-check-deploy-ci resolves security.W019 for real;
# ver openspec/changes/archive/2026-08-28-013-check-deploy-ci/).
X_FRAME_OPTIONS = 'DENY'

# security.W008 is intentionally silenced: Nginx terminates TLS and performs
# the HTTPS redirect, so Django intentionally leaves SECURE_SSL_REDIRECT=False
# (setting it here would double-redirect and break the proxy contract).
SILENCED_SYSTEM_CHECKS = ['security.W008']

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {'anon': '100/hour', 'user': '1000/hour'},
}

# FTP de observaciones (FileObs)
FTP_OBS_HOST = os.getenv('FTP_OBS_HOST')
FTP_OBS_USER = os.getenv('FTP_OBS_USER')
FTP_OBS_PASS = os.getenv('FTP_OBS_PASS')
FTP_OBS_PORT = os.getenv('FTP_OBS_PORT', '990')


def resolve_obs_local_only(default):
    """Resuelve OBS_LOCAL_ONLY a partir del default que impone el perfil.

    Flag derivada a import-time: en DEBUG local (no producción) el home sirve
    las simulaciones SYNOP locales en vez de ir al FTP de observaciones. Espejo
    de DEBUG_TOOLBAR_ENABLED: NUNCA releer DEBUG a request-time (spec 022:74-78).
    La variable de entorno OBS_LOCAL_ONLY tiene prioridad sobre el default.
    """
    return (
        default
        if 'OBS_LOCAL_ONLY' not in os.environ
        else os.getenv('OBS_LOCAL_ONLY', '0') in ('1', 'true', 'True', 'yes')
    )


SPECTACULAR_SETTINGS = {
    'TITLE': 'API Centro Meteorológico Camagüey',
    'DESCRIPTION': 'Documentación de la API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
}

# CORS
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(
        ','
    )
    if o.strip()
]
CORS_ALLOW_CREDENTIALS = True
CORS_URLS_REGEX = r'^/api/.*$'

# Email
# Path del backend de consola, compartido por los perfiles: `dev` lo usa como
# default y `production` lo rechaza. Minúscula a propósito, igual que
# `whitenoise_middleware`: en MAYÚSCULAS sería un setting y Django lo copiaría al
# objeto `settings`. Comparar el path (y no importar la clase) es lo que permite
# usarlo como constante sin arrastrar imports de mail a la importación de settings.
console_email_backend = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

# LDAP
if os.getenv('LDAP_SERVER_URI'):
    AUTHENTICATION_BACKENDS = [
        'apps.user_auth.backends.LDAP3Backend',
        'django.contrib.auth.backends.ModelBackend',
    ]

    logger = logging.getLogger('ldap3_auth')
    logger.addHandler(logging.StreamHandler())
    # El nivel es la única decisión de perfil de este bloque: `dev.py` lo sube
    # a DEBUG. Aquí no se puede ramificar sobre DEBUG (ver la regla del módulo).
    logger.setLevel(logging.INFO)

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{levelname} {asctime} {module} {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'loggers': {
        '': {'handlers': ['console'], 'level': 'INFO'},
        'django': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
