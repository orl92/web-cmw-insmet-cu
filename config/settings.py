"""
Django settings for Centro Meteorológico Provincial Camagüey
"""

import logging
import os
from pathlib import Path

from cryptography.fernet import Fernet
from django.contrib.messages import constants as messages
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

IS_PRODUCTION = 'PRODUCTION' in os.environ

DEBUG = os.getenv('DEBUG', 'True') == 'True'


def decrypt_secret_key(encrypted_secret_key, encryption_key):
    cipher_suite = Fernet(encryption_key.encode())
    return cipher_suite.decrypt(encrypted_secret_key.encode()).decode()


SECRET_KEY = decrypt_secret_key(
    os.getenv('SECRET_KEY'),
    os.getenv('ENCRYPTION_KEY'),
)

# Security
if not DEBUG:
    SECURE_SSL_REDIRECT = False
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(',') if o.strip()]

if external_hostname := os.getenv('EXTERNAL_HOSTNAME', ''):
    domain = external_hostname.replace('https://', '').replace('http://', '').split('/')[0].split(':')[0]
    if domain not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(domain)
    schemes = ['http://', 'https://'] if not DEBUG else ['http://']
    for scheme in schemes:
        origin = f"{scheme}{domain}"
        if ':' in external_hostname.split('://')[-1]:
            origin += f":{external_hostname.split(':')[-1]}"
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

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.CheckUserProfileMiddleware',
    'apps.core.middleware.MaintenanceModeMiddleware',
]

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
            ],
        },
    },
]

# Database
def get_database_config():
    if DEBUG:
        return {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }

    db_engine = os.getenv('DB_ENGINE', '').strip().lower()
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


DATABASES = get_database_config()

# Auth
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/login/'

GROUP_PERMISSION_EXCLUDED_APPS = [
    "auth", "user_auth", "admin", "contenttypes", "sessions", "messages",
    "staticfiles",
]
GROUP_PERMISSION_APP_MERGE = {
    "auth": "user_auth",
}
GROUP_PERMISSION_MODEL_MERGE = {
    "Pronóstico": "Pronóstico",
    "Pronóstico por Región": "Pronóstico",
    "Día Extendido": "Pronóstico",
    "Factura": "Facturacion",
    "Item": "Facturacion",
    "Correo": "Lista de correo",
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

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

if IS_PRODUCTION:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
else:
    STATICFILES_STORAGE = None

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
if not MEDIA_ROOT.exists():
    MEDIA_ROOT.mkdir(parents=True)

X_FRAME_OPTIONS = 'SAMEORIGIN'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_RATES': {'anon': '100/hour', 'user': '1000/hour'},
}

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
CORS_ALLOWED_ORIGINS = [o.strip() for o in os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(',') if o.strip()]
CORS_ALLOW_CREDENTIALS = True
CORS_URLS_REGEX = r'^/api/.*$'

# Email
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
    logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

# WhiteNoise
if IS_PRODUCTION:
    if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
        MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
elif 'whitenoise.middleware.WhiteNoiseMiddleware' in MIDDLEWARE:
    MIDDLEWARE.remove('whitenoise.middleware.WhiteNoiseMiddleware')

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

