import getpass
import sys
from datetime import datetime

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key

CUSTOM_EMAIL_BACKEND = 'config.custom_email_backend.CustomSTARTTLSBackend'


class Command(BaseCommand):
    help = 'Genera .env interactivamente. --production/--development para modo no interactivo.'

    def add_arguments(self, parser):
        parser.add_argument('--production', action='store_true', help='Producción (no interactivo)')
        parser.add_argument(
            '--development', action='store_true', help='Desarrollo (no interactivo)'
        )

    # ------------------------------------------------------------------
    # Utilidad de entrada interactiva (con fallback a default en EOF)
    # ------------------------------------------------------------------
    def prompt(self, label, default='', secret=False):
        suffix = f' [{default}]' if default not in ('', None) else ''
        try:
            if secret:
                self.stdout.write(f'{label}{suffix}: ', ending='')
                val = getpass.getpass('') or default
            else:
                self.stdout.write(f'{label}{suffix}: ', ending='')
                val = input('') or default
        except EOFError:
            val = default
        return val

    def prompt_bool(self, label, default=True):
        default_str = 's' if default else 'n'
        ans = self.prompt(f'{label} (s/n)', default_str).strip().lower()
        if ans in ('', default_str):
            return default
        return ans == 's'

    def handle(self, *args, **options):
        if options['production']:
            production = True
            interactive = False
        elif options['development']:
            production = False
            interactive = False
        else:
            choice = self.prompt('¿Entorno? (1) Producción   (2) Desarrollo', '2')
            production = choice.strip() == '1'
            interactive = True

        env_path = settings.BASE_DIR / '.env'
        if env_path.exists():
            self.stdout.write(
                self.style.WARNING('⚠️ El archivo .env ya existe. No se sobrescribirá.')
            )
            return

        secret_key = get_random_secret_key()
        encryption_key = Fernet.generate_key()
        cipher_suite = Fernet(encryption_key)
        encrypted_secret_key = cipher_suite.encrypt(secret_key.encode()).decode()

        try:
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write('# ============================================================\n')
                f.write('# ARCHIVO DE CONFIGURACIÓN DEL PROYECTO\n')
                f.write('# ============================================================\n')
                f.write(
                    '# Generado automáticamente el '
                    + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    + '\n'
                )
                f.write('# ============================================================\n\n')

                # --- Configuración básica ---
                f.write('# =====================\n')
                f.write('# CONFIGURACIÓN BÁSICA (REQUERIDA)\n')
                f.write('# =====================\n')
                f.write(f'DEBUG={"False" if production else "True"}\n')
                f.write(f'SECRET_KEY={encrypted_secret_key}\n')
                f.write(f'ENCRYPTION_KEY={encryption_key.decode()}\n\n')

                # --- Dominio ---
                f.write('# =====================\n')
                f.write('# CONFIGURACIÓN DE DOMINIO\n')
                f.write('# =====================\n')
                if interactive:
                    hostname = self.prompt(
                        'Dominio externo (sin http://)',
                        'cmw.insmet.cu' if production else 'localhost',
                    )
                    allowed = self.prompt(
                        'ALLOWED_HOSTS (separados por comas)',
                        'localhost,127.0.0.1' if not production else hostname,
                    )
                    csrf = self.prompt(
                        'CSRF_TRUSTED_ORIGINS (separados por comas)',
                        'http://localhost:8000,http://127.0.0.1:8000'
                        if not production
                        else f'https://{hostname}',
                    )
                else:
                    hostname = 'cmw.insmet.cu' if production else 'localhost'
                    allowed = 'localhost,127.0.0.1' if not production else hostname
                    csrf = (
                        'http://localhost:8000,http://127.0.0.1:8000'
                        if not production
                        else f'https://{hostname}'
                    )
                if production:
                    f.write(f'EXTERNAL_HOSTNAME={hostname}\n')
                else:
                    f.write(f'# EXTERNAL_HOSTNAME={hostname}\n')
                f.write(f'ALLOWED_HOSTS={allowed}\n')
                f.write(f'CSRF_TRUSTED_ORIGINS={csrf}\n\n')

                # --- Email ---
                self._write_email_config(f, production, interactive)

                # --- FTP observaciones ---
                self._write_ftp_config(f, interactive)

                # --- Base de datos ---
                self._write_database_config(f, production, interactive)

                # --- LDAP ---
                self._write_ldap_config(f, production, interactive)

                # --- CORS ---
                f.write('# =====================\n')
                f.write('# CONFIGURACIÓN CORS\n')
                f.write('# =====================\n')
                if production:
                    f.write(f'CORS_ALLOWED_ORIGINS=https://{hostname},https://www.{hostname}\n\n')
                else:
                    f.write('CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000\n\n')

                # --- Logging ---
                f.write('# =====================\n')
                f.write('# CONFIGURACIÓN DE LOGGING\n')
                f.write('# =====================\n')
                f.write('LOG_LEVEL=INFO\n')
                f.write('LOG_FILE=/var/log/cmw/app.log\n\n')

                # --- Cache ---
                f.write('# =====================\n')
                f.write('# CONFIGURACIÓN DE CACHE\n')
                f.write('# =====================\n')
                f.write('# CACHE_BACKEND=django.core.cache.backends.redis.RedisCache\n')
                f.write('# CACHE_LOCATION=redis://localhost:6379/1\n')
                f.write('CACHE_BACKEND=django.core.cache.backends.locmem.LocMemCache\n\n')

            self.stdout.write(self.style.SUCCESS('✅ Archivo .env creado exitosamente'))
            self.stdout.write(f'📁 Ubicación: {env_path}')
            self.stdout.write('🔑 SECRET_KEY y ENCRYPTION_KEY generadas automáticamente.')

            if production:
                self.stdout.write(
                    self.style.WARNING('\n⚠️ Revise las variables críticas en el .env generado.')
                )
            self.stdout.write('\n✏️ Puede editarlo con cualquier editor de texto:')
            self.stdout.write(f'  nano {env_path}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al crear .env: {e}'))
            sys.exit(1)

    # ------------------------------------------------------------------
    # Secciones
    # ------------------------------------------------------------------
    def _write_email_config(self, f, production, interactive):
        f.write('# =====================\n')
        f.write('# CONFIGURACIÓN DE EMAIL\n')
        f.write('# =====================\n')
        if interactive:
            autofirmado = self.prompt_bool(
                '¿El servidor de correo usa certificado autofirmado?', default=True
            )
            use_tls = self.prompt_bool('¿Usar TLS?', default=True)
            host = self.prompt('EMAIL_HOST', 'smtp.tu-dominio.com')
            port = self.prompt('EMAIL_PORT', '587')
            user = self.prompt('EMAIL_HOST_USER', 'user@tu-dominio.com')
            email_cred = self.prompt('EMAIL_HOST_PASSWORD', 'contraseña_segura', secret=True)
            from_email = self.prompt(
                'DEFAULT_FROM_EMAIL', "'Centro Meteorológico Camagüey <user@tu-dominio.com>'"
            )
        else:
            autofirmado = production
            use_tls = True
            host = 'smtp.tu-dominio.com'
            port = '587'
            user = 'user@tu-dominio.com'
            email_cred = 'tu_contraseña_segura'
            from_email = "'Centro Meteorológico Camagüey <user@tu-dominio.com>'"

        if autofirmado:
            f.write(f'EMAIL_BACKEND={CUSTOM_EMAIL_BACKEND}\n')
        elif production:
            f.write('EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend\n')
        else:
            f.write('EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend\n')
        f.write(f'EMAIL_USE_TLS={str(use_tls)}\n')
        f.write(f'EMAIL_HOST={host}\n')
        f.write(f'EMAIL_PORT={port}\n')
        f.write(f'EMAIL_HOST_USER={user}\n')
        f.write(f'EMAIL_HOST_PASSWORD={email_cred}\n')
        f.write(f'DEFAULT_FROM_EMAIL={from_email}\n')
        f.write('EMAIL_USE_SSL=False\n\n')

    def _write_ftp_config(self, f, interactive):
        f.write('# =====================\n')
        f.write('# FTP DE OBSERVACIONES (FileObs)\n')
        f.write('# =====================\n')
        f.write('# Credenciales del servidor FTP de observaciones.\n')
        f.write('# Reemplazar con los valores REALES (no commitear el .env).\n')
        if interactive:
            host = self.prompt('FTP_OBS_HOST', 'host_ftp')
            user = self.prompt('FTP_OBS_USER', 'usuario_ftp')
            ftp_cred = self.prompt('FTP_OBS_PASS', 'contraseña_ftp', secret=True)
            port = self.prompt('FTP_OBS_PORT', '990')
        else:
            host = 'host_ftp'
            user = 'usuario_ftp'
            ftp_cred = 'contraseña_ftp'
            port = '990'
        f.write(f'FTP_OBS_HOST={host}\n')
        f.write(f'FTP_OBS_USER={user}\n')
        f.write(f'FTP_OBS_PASS={ftp_cred}\n')
        f.write(f'FTP_OBS_PORT={port}\n\n')

    def _write_database_config(self, f, production, interactive):
        f.write('# =====================\n')
        f.write('# CONFIGURACIÓN DE BASE DE DATOS\n')
        f.write('# =====================\n')
        if production:
            if interactive:
                engine = self.prompt('DB_ENGINE', 'postgresql')
                name = self.prompt('DB_NAME', 'web_db')
                user = self.prompt('DB_USER', 'postgres')
                db_cred = self.prompt('DB_PASS', 'contraseña_segura', secret=True)
                host = self.prompt('DB_HOST', 'localhost')
                port = self.prompt('DB_PORT', '5432')
            else:
                engine, name, user, db_cred, host, port = (
                    'postgresql',
                    'web_db',
                    'postgres',
                    'contraseña_segura',
                    'localhost',
                    '5432',
                )
            f.write(f'DB_ENGINE={engine}\n')
            f.write(f'DB_NAME={name}\n')
            f.write(f'DB_USER={user}\n')
            f.write(f'DB_PASS={db_cred}\n')
            f.write(f'DB_HOST={host}\n')
            f.write(f'DB_PORT={port}\n')
            f.write('DB_SSL_MODE=prefer\n')
            f.write('# DB_SSL_ROOT_CERT=/ruta/ca.crt\n\n')
        else:
            f.write('# Desarrollo usa SQLite por defecto\n')
            f.write('DB_ENGINE=sqlite3\n')
            f.write('# Para PostgreSQL descomentar:\n')
            f.write('# DB_ENGINE=postgresql\n')
            f.write('# DB_NAME=web_db_dev\n')
            f.write('# DB_USER=postgres\n')
            f.write('# DB_PASS=postgres\n')
            f.write('# DB_HOST=localhost\n')
            f.write('# DB_PORT=5432\n\n')

    def _write_ldap_config(self, f, production, interactive):
        f.write('# =====================\n')
        f.write('# CONFIGURACIÓN LDAP (OPCIONAL)\n')
        f.write('# =====================\n')
        usar_ldap = self.prompt_bool('¿Configurar LDAP?', default=False) if interactive else False
        if not usar_ldap:
            f.write('# LDAP desactivado. Para activar, completa los valores abajo.\n')
            f.write('# LDAP_SERVER_URI=ldap://localhost:389\n')
            f.write('# LDAP_START_TLS=False\n')
            f.write('# LDAP_BIND_DN=cn=admin,dc=example,dc=org\n')
            f.write('# LDAP_BIND_PASSWORD=admin\n')
            f.write('# LDAP_USER_SEARCH_BASE=ou=users,dc=example,dc=org\n')
            f.write('# LDAP_GROUP_SEARCH_BASE=ou=groups,dc=example,dc=org\n')
            f.write('# LDAP_STAFF_GROUP=cn=staff,ou=groups,dc=example,dc=org\n')
            f.write('# LDAP_SUPERUSER_GROUP=cn=superuser,ou=groups,dc=example,dc=org\n\n')
            return
        if production:
            f.write('# --- OpenLDAP (Linux) ---\n')
            f.write('LDAP_SERVER_URI=ldap://dc.cmw.insmet.cu:389\n')
            f.write('LDAP_START_TLS=True\n')
            f.write('LDAP_BIND_DN=CN=linux,CN=Users,DC=cmw,DC=insmet,DC=cu\n')
            f.write('LDAP_BIND_PASSWORD=tu_contraseña_ldap\n')
            f.write('LDAP_USER_SEARCH_BASE=OU=CMW,DC=cmw,DC=insmet,DC=cu\n')
            f.write('LDAP_GROUP_SEARCH_BASE=OU=CMW,DC=cmw,DC=insmet,DC=cu\n')
            f.write('LDAP_STAFF_GROUP=cn=staff,OU=CMW,DC=cmw,DC=insmet,DC=cu\n')
            f.write('LDAP_SUPERUSER_GROUP=cn=superuser,OU=CMW,DC=cmw,DC=insmet,DC=cu\n')
        else:
            f.write('# --- LDAP desarrollo ---\n')
            f.write('LDAP_SERVER_URI=ldap://localhost:389\n')
            f.write('LDAP_START_TLS=False\n')
            f.write('LDAP_BIND_DN=cn=admin,dc=example,dc=org\n')
            f.write('LDAP_BIND_PASSWORD=admin\n')
            f.write('LDAP_USER_SEARCH_BASE=ou=users,dc=example,dc=org\n')
            f.write('LDAP_GROUP_SEARCH_BASE=ou=groups,dc=example,dc=org\n')
            f.write('LDAP_STAFF_GROUP=cn=staff,ou=groups,dc=example,dc=org\n')
            f.write('LDAP_SUPERUSER_GROUP=cn=superuser,ou=groups,dc=example,dc=org\n')
        f.write('# LDAP_USER_ATTR_MAP=first_name:givenName,last_name:sn,email:mail\n')
        f.write('# LDAP_CACHE_TIMEOUT=3600\n\n')
