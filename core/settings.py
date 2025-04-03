"""
Django settings for Centro Meteorológico Camagüey

Más información: https://web.cmw.insmet.cu
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from str2bool import str2bool
from django.core.management.utils import get_random_secret_key
from django.core.exceptions import ImproperlyConfigured
from django.contrib.messages import constants as messages

# =====================
# 1. INITIAL SETUP
# =====================
BASE_DIR = Path(__file__).resolve().parent.parent

def create_default_env(production=False):
    """Crea un archivo .env con valores por defecto usando UTF-8"""
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        return
    
    print("\n🔧 Creando archivo .env automáticamente...")
    
    secret_key = get_random_secret_key()
    
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(f"# Configuración {'producción' if production else 'desarrollo'}\n")
            f.write(f"DEBUG={'False' if production else 'True'}\n")
            f.write(f"SECRET_KEY={secret_key}\n")
            f.write("ALLOWED_HOSTS=localhost,127.0.0.1\n")
            f.write("CSRF_TRUSTED_ORIGINS=http://localhost:8000\n")
            
            if production:
                f.write("\n# Configuración de producción\n")
                f.write("# EXTERNAL_HOSTNAME=tu-dominio-real.com\n")
                f.write("DB_ENGINE=postgresql\n")
                f.write("DB_NAME=meteorologia\n")
                f.write("DB_USER=usuario_bd\n")
                f.write("DB_PASS=contraseña_segura\n")
                f.write("DB_HOST=localhost\n")
                f.write("DB_PORT=5432\n")
                f.write("EMAIL_HOST=smtp.office365.com\n")
                f.write("EMAIL_PORT=587\n")
                f.write("EMAIL_HOST_USER=tu@cmw.insmet.cu\n")
                f.write("EMAIL_HOST_PASSWORD=tu_contraseña\n")
                f.write("DEFAULT_FROM_EMAIL=no-reply@cmw.insmet.cu\n")
        
        print(f"✅ Archivo .env creado con valores para {'producción' if production else 'desarrollo'}")
        print(f"🔑 SECRET_KEY generada: {secret_key[:15]}... (Guárdala en un lugar seguro)")
    except Exception as e:
        print(f"❌ Error al crear .env: {str(e)}")
        sys.exit(1)

# Detectar entorno
IS_PRODUCTION = 'PRODUCTION' in os.environ or '--production' in sys.argv

# Crear .env si no existe
create_default_env(production=IS_PRODUCTION)

# Cargar variables de entorno con UTF-8
try:
    load_dotenv(encoding='utf-8')
except UnicodeDecodeError:
    print("❌ Error: El archivo .env tiene problemas de codificación. Por favor:")
    print("1. Elimina el archivo .env existente")
    print("2. Vuelve a ejecutar para generar uno nuevo")
    sys.exit(1)

# =====================
# 2. CORE SETTINGS
# =====================
DEBUG = str2bool(os.getenv('DEBUG', 'False' if IS_PRODUCTION else 'True'))

def validate_environment():
    """Valida la configuración esencial"""
    errors = []
    
    if not os.getenv('SECRET_KEY'):
        errors.append("🚨 ERROR: Falta SECRET_KEY en .env")
    
    if not DEBUG and not os.getenv('EXTERNAL_HOSTNAME'):
        errors.append("🚨 ERROR: Para producción debe configurar EXTERNAL_HOSTNAME en .env")
        errors.append("💡 Ejemplo: EXTERNAL_HOSTNAME=ace3.aceitecmg.alinet.cu")
    
    if errors:
        print("\n".join(errors))
        print("\n❌ Servidor no puede iniciar - Corrija estas configuraciones")
        sys.exit(1)

validate_environment()

SECRET_KEY = os.getenv('SECRET_KEY')

# =====================
# 3. SECURITY SETTINGS
# =====================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# =====================
# 4. HOST CONFIGURATION
# =====================
ALLOWED_HOSTS = [
    h.strip() 
    for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') 
    if h.strip()
]

CSRF_TRUSTED_ORIGINS = [
    o.strip() 
    for o in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000').split(',') 
    if o.strip()
]

# Configuración dinámica del dominio
if EXTERNAL_HOSTNAME := os.getenv('EXTERNAL_HOSTNAME'):
    domain = EXTERNAL_HOSTNAME.replace('https://', '').replace('http://', '').split('/')[0].split(':')[0]
    
    if domain not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(domain)
    
    schemes = ['http://', 'https://'] if not DEBUG else ['http://']
    for scheme in schemes:
        origin = f"{scheme}{domain}"
        if ':' in EXTERNAL_HOSTNAME.split('://')[-1]:
            origin += f":{EXTERNAL_HOSTNAME.split(':')[-1]}"
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)

# =====================
# 5. APPLICATION CONFIG
# =====================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'drf_redesign',
    'rest_framework',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'api.apps.ApiConfig',
    'home.apps.HomeConfig',
    'login.apps.LoginConfig',
    'accounts.apps.AccountsConfig',
    'dashboard.apps.DashboardConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.check_user_profile.CheckUserProfileMiddleware',
    'dashboard.middleware.maintenance_mode.MaintenanceModeMiddleware',
]

ROOT_URLCONF = 'core.urls'

# =====================
# 6. TEMPLATES
# =====================
HOME_TEMPLATES = os.path.join(BASE_DIR, 'templates')

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
                'dashboard.context_processors.notification_counts',
            ],
        },
    },
]
    
WSGI_APPLICATION = 'core.wsgi.application'

# =====================
# 7. DATABASE
# =====================
DATABASES = {
    'default': {
        'ENGINE': f"django.db.backends.{os.getenv('DB_ENGINE', 'sqlite3')}",
        'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASS', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
        'CONN_MAX_AGE': 600 if not DEBUG else 0,
        'OPTIONS': {
            'sslmode': 'require' if not DEBUG else 'prefer',
        } if 'postgres' in os.getenv('DB_ENGINE', '') else {}
    }
}

# =====================
# 8. PASSWORD VALIDATION
# =====================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =====================
# 9. INTERNATIONALIZATION 
# =====================
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Havana'
USE_I18N = True
USE_TZ = True

# =====================
# 10. STATIC FILES
# =====================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage' if not DEBUG else None

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
    
X_FRAME_OPTIONS = 'SAMEORIGIN'

# =====================
# 11. AUTH SETTINGS
# =====================
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
LOGIN_URL = '/login/'

MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# =====================
# 12. REST FRAMEWORK
# =====================
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
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

# =====================
# 13. EMAIL CONFIGURATION
# =====================
EMAIL_USE_TLS = str2bool(os.getenv('EMAIL_USE_TLS', 'True'))
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

if 'EMAIL_BACKEND' in os.environ:
    EMAIL_BACKEND = os.environ['EMAIL_BACKEND']
elif 'CUSTOM_EMAIL_BACKEND' in os.environ:
    EMAIL_BACKEND = os.environ['CUSTOM_EMAIL_BACKEND']
    EMAIL_USE_SSL = False

# =====================
# 14. FINAL VALIDATION
# =====================
if not DEBUG:
    required = {
        'SECRET_KEY': SECRET_KEY,
        'ALLOWED_HOSTS': ALLOWED_HOSTS,
        'EMAIL_HOST': os.getenv('EMAIL_HOST')
    }
    if not all(required.values()):
        missing = [k for k, v in required.items() if not v]
        raise ImproperlyConfigured(f"Falta configuración de producción: {', '.join(missing)}")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'