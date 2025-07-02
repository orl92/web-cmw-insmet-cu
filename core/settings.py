"""
Django settings for Centro Meteorológico Camagüey

Más información: https://web.cmw.insmet.cu
"""

import os
import sys
from pathlib import Path

from cryptography.fernet import Fernet
from django.contrib.messages import constants as messages
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv
from str2bool import str2bool

# Para LDAP
import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType
import logging

# =====================
# 1. INITIAL SETUP
# =====================
BASE_DIR = Path(__file__).resolve().parent.parent

# Detectar entorno al inicio
IS_PRODUCTION = 'PRODUCTION' in os.environ or '--production' in sys.argv


def create_default_env(production=False):
    """Crea un archivo .env con valores por defecto y guías para el usuario"""
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        return

    print("\n🔧 Creando archivo .env automáticamente con valores iniciales...")

    secret_key = get_random_secret_key()
    encryption_key = Fernet.generate_key()
    cipher_suite = Fernet(encryption_key)
    encrypted_secret_key = cipher_suite.encrypt(secret_key.encode()).decode()

    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            # 1. Configuración básica
            f.write("# =====================\n")
            f.write("# CONFIGURACIÓN BÁSICA (REQUERIDA)\n")
            f.write("# =====================\n")
            f.write(f"DEBUG={'False' if production else 'True'}\n")
            f.write(f"SECRET_KEY={encrypted_secret_key}\n")
            f.write(f"ENCRYPTION_KEY={encryption_key.decode()}\n\n")

            # 2. Configuración de email (solo desarrollo)
            if not production:
                f.write("# =====================\n")
                f.write("# CONFIGURACIÓN DE EMAIL PARA DESARROLLO\n")
                f.write("# =====================\n")
                f.write("EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend\n")
                f.write("# EmailBackend que muestra los correos en la consola\n\n")
                f.write("# Comenta EMAIL_BACKEND y Descomenta el resto para usar Configuracion de server real\n\n")
                f.write("# EMAIL_USE_TLS=True\n")
                f.write("# EMAIL_HOST=smtp.tu-dominio.com\n")
                f.write("# EMAIL_PORT=587\n")
                f.write("# EMAIL_HOST_USER=user@tu-dominio.com\n")
                f.write("# EMAIL_HOST_PASSWORD=tu_contraseña_segura\n")
                f.write("# DEFAULT_FROM_EMAIL='Centro Meteorológico Camagüey <user@tu-dominio.com>'\n")
                f.write("# CUSTOM_EMAIL_BACKEND=core.custom_email_backend.CustomSTARTTLSBackend\n")
                f.write("# EMAIL_USE_SSL=False\n\n")

            # 3. Configuración para producción
            if production:
                # 3.1. Configuración de dominio
                f.write("# =====================\n")
                f.write("# CONFIGURACIÓN DE DOMINIO (PRODUCCIÓN - ⚠️ MODIFICAR! ⚠️)\n")
                f.write("# =====================\n")
                f.write("# Ejemplo: tu-dominio.com (sin http://)\n")
                f.write("EXTERNAL_HOSTNAME=cmw.insmet.cu\n\n")
                f.write("# Opcional: Puede definir manualmente estos valores si necesita configuraciones especiales\n")
                f.write("# ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com\n")
                f.write("# CSRF_TRUSTED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com\n\n")

                # 3.2 Email
                f.write("# =====================\n")
                f.write("# CONFIGURACIÓN DE EMAIL (PRODUCCIÓN - ⚠️ MODIFICAR!)\n")
                f.write("# =====================\n")
                f.write("# ⚠️ DEBE CONFIGURAR LOS VALORES REALES ⚠️\n")
                f.write("EMAIL_USE_TLS=True\n")
                f.write("EMAIL_HOST=smtp.tu-dominio.com\n")
                f.write("EMAIL_PORT=587\n")
                f.write("EMAIL_HOST_USER=user@tu-dominio.com\n")
                f.write("EMAIL_HOST_PASSWORD=tu_contraseña_segura\n")
                f.write("DEFAULT_FROM_EMAIL='Centro Meteorológico Camagüey <user@tu-dominio.com>'\n")
                f.write("CUSTOM_EMAIL_BACKEND=core.custom_email_backend.CustomSTARTTLSBackend\n")
                f.write("EMAIL_USE_SSL=False\n")

                # 3.3 Base de datos
                f.write("# =====================\n")
                f.write("# BASE DE DATOS (PRODUCCIÓN - ⚠️ MODIFICAR!)\n")
                f.write("# =====================\n")
                f.write("DB_ENGINE=postgresql  # Opciones: postgresql, mysql\n")
                f.write("DB_NAME=web_db\n")
                f.write("DB_USER=postgres\n")
                f.write("DB_PASS=contraseña_segura\n")
                f.write("DB_HOST=localhost\n")
                f.write("DB_PORT=5432  # 3306 para MySQL\n")
                f.write("# Configuración SSL PostgreSQL:\n")
                f.write("DB_SSL_MODE=prefer  # disable, allow, prefer, require, verify-ca, verify-full\n")
                f.write("# DB_SSL_ROOT_CERT=/ruta/ca.crt\n\n")
                f.write("# Configuración SSL MySQL:\n")
                f.write("# DB_SSL_MODE=PREFERRED  # DISABLED, PREFERRED, REQUIRED, VERIFY_CA, VERIFY_IDENTITY\n")
                f.write("# DB_SSL_CA=/ruta/ca.pem\n")
                f.write("# DB_SSL_CERT=/ruta/client-cert.pem\n")
                f.write("# DB_SSL_KEY=/ruta/client-key.pem\n")
            else:
                f.write("# Configuración para desarrollo (puede modificarse si usa otros hosts)\n")
                f.write("ALLOWED_HOSTS=localhost,127.0.0.1\n")
                f.write("CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000\n\n")
                f.write("# EXTERNAL_HOSTNAME=cmw.insmet.cu\n\n")

        # Mensajes post-creación
        print("\n✅ Archivo .env creado exitosamente")
        print("🔑 SECRET_KEY generada automáticamente.")

        if production:
            print("\n⚠️ ATENCIÓN: Debe editar manualmente estas variables CRÍTICAS para producción:")
            print("  - EXTERNAL_HOSTNAME (debe ser su dominio real sin http://)")
            print("\n💡 El sistema automáticamente generará:")
            print("  - ALLOWED_HOSTS basado en EXTERNAL_HOSTNAME")
            print("  - Configuración de EMAIL (Modificar por servidor SMTP real)")
            print("  - Configuración de BASE DE DATOS (Modificar por credenciales reales)")
            print("  - CSRF_TRUSTED_ORIGINS (con https://)")
            print("\n⚙️ Si necesita configuraciones especiales, puede definir manualmente:")
            print("  - ALLOWED_HOSTS para múltiples dominios/subdominios")
            print("  - CSRF_TRUSTED_ORIGINS para protocolos/puertos específicos")

            print("\n💡 RECOMENDACIONES PARA PRODUCCIÓN:")
            print("  - Use PostgreSQL o MySQL como motor de base de datos")
            print("  - Configure backups automáticos de la base de datos")
            print("  - Revise los permisos de los archivos sensibles")

        print("\n✏️ Puede editarlo con:")
        print("  - VS Code: 'code .env'")
        print("  - Nano: 'nano .env'")
        print("  - Cualquier editor de texto")

    except Exception as e:
        print(f"\n❌ Error al crear .env: {str(e)}")
        print("ℹ️ Posible solución: Verifique los permisos de escritura en el directorio")
        sys.exit(1)


def decrypt_secret_key(encrypted_secret_key, encryption_key):
    cipher_suite = Fernet(encryption_key.encode())
    return cipher_suite.decrypt(encrypted_secret_key.encode()).decode()


# Crear .env si no existe
create_default_env(production=IS_PRODUCTION)

# Cargar variables de entorno
try:
    load_dotenv(encoding='utf-8')
except Exception as e:
    print(f"\n❌ Error al cargar .env: {str(e)}")
    print("ℹ️ Posible solución: Elimine el archivo .env y vuelva a ejecutar")
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

    if not DEBUG:
        if not os.getenv('EXTERNAL_HOSTNAME'):
            errors.append("🚨 ERROR: Para producción debe configurar EXTERNAL_HOSTNAME en .env")

        # Validar formato del dominio
        if (hostname := os.getenv('EXTERNAL_HOSTNAME')) and any(
                c in hostname for c in ('http://', 'https://', '/', ':')
        ):
            errors.append("🚨 ERROR: EXTERNAL_HOSTNAME debe ser solo el dominio (ej: cmw.insmet.cu)")

    if errors:
        print("\n".join(errors))
        print("\n❌ Servidor no puede iniciar - Corrija estas configuraciones")
        sys.exit(1)


def validate_database_config():
    """Valida la configuración de base de datos para producción"""
    if not IS_PRODUCTION:
        return

    # Validar variables obligatorias para todos los motores
    required_vars = ['DB_ENGINE', 'DB_NAME', 'DB_USER', 'DB_PASS', 'DB_HOST']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"\n🚨 ERROR: Faltan variables esenciales de BD: {', '.join(missing_vars)}")
        sys.exit(1)

    db_engine = os.getenv('DB_ENGINE').lower()

    # Validar motor de BD soportado
    if db_engine not in ['postgresql', 'mysql']:
        print(f"\n🚨 ERROR: Motor de BD no soportado: {db_engine}")
        print("💡 Use 'postgresql' o 'mysql' en producción")
        sys.exit(1)

    # Validaciones específicas para PostgreSQL
    if db_engine == 'postgresql':
        ssl_mode = os.getenv('DB_SSL_MODE', 'prefer').lower()

        if ssl_mode in ['verify-ca', 'verify-full']:
            if not os.getenv('DB_SSL_ROOT_CERT'):
                print("\n🚨 ERROR: PostgreSQL en modo verify-ca/verify-full requiere:")
                print("💡 Debe configurar DB_SSL_ROOT_CERT con la ruta al certificado CA")
                sys.exit(1)

            if not os.path.exists(os.getenv('DB_SSL_ROOT_CERT')):
                print(f"\n🚨 ERROR: No se encuentra el certificado CA en: {os.getenv('DB_SSL_ROOT_CERT')}")
                print("💡 Verifique la ruta en DB_SSL_ROOT_CERT")
                sys.exit(1)

    # Validaciones específicas para MySQL
    elif db_engine == 'mysql':
        ssl_mode = os.getenv('DB_SSL_MODE', 'PREFERRED').upper()

        if ssl_mode in ['VERIFY_CA', 'VERIFY_IDENTITY']:
            missing_certs = [var for var in ['DB_SSL_CA', 'DB_SSL_CERT', 'DB_SSL_KEY'] if not os.getenv(var)]

            if missing_certs:
                print(f"\n🚨 ERROR: MySQL en modo {ssl_mode} requiere: {', '.join(missing_certs)}")
                sys.exit(1)

            for cert_var in ['DB_SSL_CA', 'DB_SSL_CERT', 'DB_SSL_KEY']:
                if not os.path.exists(os.getenv(cert_var)):
                    print(f"\n🚨 ERROR: No se encuentra el certificado {cert_var} en: {os.getenv(cert_var)}")
                    sys.exit(1)

    # Advertencia sobre modos SSL inseguros en producción
    if db_engine == 'postgresql' and os.getenv('DB_SSL_MODE', 'prefer') in ['disable', 'allow']:
        print("\n⚠️ ADVERTENCIA: PostgreSQL está usando un modo SSL poco seguro en producción")
        print("💡 Recomendado: Usar al menos 'require' para conexiones encriptadas")

    elif db_engine == 'mysql' and os.getenv('DB_SSL_MODE', 'PREFERRED').upper() in ['DISABLED']:
        print("\n⚠️ ADVERTENCIA: MySQL está configurado sin SSL en producción")
        print("💡 Recomendado: Usar al menos 'REQUIRED' para conexiones encriptadas")


# Validar configuración
validate_environment()
validate_database_config()

SECRET_KEY = os.getenv('SECRET_KEY')

# =====================
# 3. SECURITY SETTINGS
# =====================
if not DEBUG:
    SECURE_SSL_REDIRECT = False  # Se manejan con nginx
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
    for o in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(',')
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
# 7. DATABASE CONFIGURATION
# =====================
def get_database_config():
    """Configuración dinámica para PostgreSQL y MySQL con soporte SSL"""
    if DEBUG:
        return {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }

    db_engine = os.getenv('DB_ENGINE', '').strip().lower()
    if db_engine not in ['postgresql', 'mysql']:
        print("\n🚨 ERROR: Motor de BD no válido (use postgresql o mysql)")
        sys.exit(1)

    # Configuración común
    db_config = {
        'ENGINE': f'django.db.backends.{db_engine}',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASS'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432' if db_engine == 'postgresql' else '3306'),
        'CONN_MAX_AGE': 600,
    }

    # Configuración SSL para PostgreSQL
    if db_engine == 'postgresql':
        ssl_mode = os.getenv('DB_SSL_MODE', 'prefer')
        db_config['OPTIONS'] = {'sslmode': ssl_mode}

        if ssl_mode in ['verify-ca', 'verify-full']:
            if ssl_cert := os.getenv('DB_SSL_ROOT_CERT'):
                db_config['OPTIONS']['sslrootcert'] = ssl_cert
            else:
                print("\n🚨 ERROR: Se requiere DB_SSL_ROOT_CERT para verify-ca/verify-full")
                sys.exit(1)

    # Configuración SSL para MySQL
    elif db_engine == 'mysql':
        ssl_mode = os.getenv('DB_SSL_MODE', 'PREFERRED').upper()
        if ssl_mode != 'DISABLED':
            ssl_files = {
                'ca': os.getenv('DB_SSL_CA'),
                'cert': os.getenv('DB_SSL_CERT'),
                'key': os.getenv('DB_SSL_KEY')
            }

            if ssl_mode in ['VERIFY_CA', 'VERIFY_IDENTITY'] and not all(ssl_files.values()):
                print("\n🚨 ERROR: Para VERIFY_CA/VERIFY_IDENTITY necesita:")
                print("DB_SSL_CA, DB_SSL_CERT y DB_SSL_KEY")
                sys.exit(1)

            db_config['OPTIONS'] = {
                'ssl_mode': ssl_mode,
                'ssl': {k: v for k, v in ssl_files.items() if v} or None
            }

    return {'default': db_config}


DATABASES = get_database_config()

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

# Configuración diferente para desarrollo/producción
if IS_PRODUCTION:
    # Crear directorio si no existe
    if not os.path.exists(STATIC_ROOT):
        os.makedirs(STATIC_ROOT)
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
else:
    STATICFILES_STORAGE = None

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Configuración de medios
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
if not os.path.exists(MEDIA_ROOT):
    os.makedirs(MEDIA_ROOT)

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

# =====================
# 13. SPECTACULAR SETTINGS (OpenAPI)
# =====================
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
# 14. EMAIL CONFIGURATION
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
# 15. WHITENOISE CONFIGURATION
# =====================
# Solo usar WhiteNoise en producción
if IS_PRODUCTION:
    # Verificar que WhiteNoise esté correctamente configurado
    if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
        MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    print("\n🛡️ WhiteNoise habilitado para servir archivos estáticos en producción")
elif 'whitenoise.middleware.WhiteNoiseMiddleware' in MIDDLEWARE:
    # Remover WhiteNoise en desarrollo para evitar advertencias
    MIDDLEWARE.remove('whitenoise.middleware.WhiteNoiseMiddleware')

# =====================
# 16. FINAL VALIDATION
# =====================
# Variables necesarias en producción
if not DEBUG:
    required_vars = {
        'EMAIL_HOST': "Servidor SMTP para correos",
        'EMAIL_PORT': "Puerto del servidor SMTP",
        'EMAIL_HOST_USER': "Usuario para autenticación SMTP",
        'EMAIL_HOST_PASSWORD': "Contraseña para autenticación SMTP",
        'DEFAULT_FROM_EMAIL': "Email desde el que se enviarán los correos"
    }

    missing_vars = [var for var, desc in required_vars.items() if not os.getenv(var)]

    if missing_vars:
        print("\n🚨 ERROR: Faltan configuraciones requeridas para producción:")
        for var in missing_vars:
            print(f"  - {var}: {required_vars[var]}")
        print("\n💡 Edite el archivo .env con estos valores")
        sys.exit(1)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =====================
# LDAP
# =====================
# Configuración básica de LDAP
AUTH_LDAP_SERVER_URI = "ldap://dc.cmw.insmet.cu:389"  # Reemplaza con tu servidor LDAP
AUTH_LDAP_START_TLS = True  # Para habilitar STARTTLS
AUTH_LDAP_GLOBAL_OPTIONS = {
    ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,  # Para desarrollo, en producción usa OPT_X_TLS_DEMAND
    ldap.OPT_REFERRALS: 0,
}

# Credenciales para buscar usuarios
AUTH_LDAP_BIND_DN = "CN=linux,CN=Users,DC=cmw,DC=insmet,DC=cu"  # DN del usuario con permisos de búsqueda
AUTH_LDAP_BIND_PASSWORD = "100A.soledad"  # Contraseña del usuario

# Configuración de búsqueda de usuarios
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "OU=CMW,DC=cmw,DC=insmet,DC=cu",  # Base DN para buscar usuarios
    ldap.SCOPE_SUBTREE,  # Ámbito de búsqueda
    "(sAMAccountName=%(user)s)"  # Filtro de búsqueda (puede variar según tu LDAP)
)

# Configuración para mapear atributos LDAP a campos de usuario Django
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail"
}

# Configuración de grupos (opcional)
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "OU=CMW,DC=cmw,DC=insmet,DC=cu",
    ldap.SCOPE_SUBTREE,
    "(objectClass=groupOfNames)"
)
AUTH_LDAP_GROUP_TYPE = GroupOfNamesType(name_attr="cn")

# Qué hacer cuando un usuario se autentica por primera vez
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_staff": "cn=staff,OU=CMW,DC=cmw,DC=insmet,DC=cu",
    "is_superuser": "cn=superuser,OU=CMW,DC=cmw,DC=insmet,DC=cu"
}

AUTH_LDAP_FIND_GROUP_PERMS = True
AUTH_LDAP_MIRROR_GROUPS = False  # Sincroniza grupos LDAP con grupos Django

# Configuración de caché (recomendado para producción)
AUTH_LDAP_CACHE_TIMEOUT = 3600

# Configuración de autenticación
AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',  # Primero intenta LDAP
    'django.contrib.auth.backends.ModelBackend',  # Luego la base de datos local
)

logger = logging.getLogger('django_auth_ldap')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)  # Para desarrollo, en producción usa INFO o WARNING
