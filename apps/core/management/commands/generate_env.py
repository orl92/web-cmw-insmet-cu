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
        parser.add_argument(
            '--rotate-keys',
            action='store_true',
            help='Regenera SECRET_KEY/ENCRYPTION_KEY (usar si estan comprometidos)',
        )

    # ------------------------------------------------------------------
    # Utilidad de entrada interactiva (con fallback a default en EOF)
    # ------------------------------------------------------------------
    def prompt(self, label, default='', secret=False):
        effective = default
        if getattr(self, 'existing', None):
            effective = self.existing.get(label, default)
        suffix = ''
        if not secret and effective not in ('', None):
            suffix = f' [{effective}]'
        try:
            if secret:
                self.stdout.write(f'{label}: ', ending='')
                val = getpass.getpass('') or effective
            else:
                self.stdout.write(f'{label}{suffix}: ', ending='')
                val = input('') or effective
        except EOFError:
            val = effective
        return val

    def _load_env(self, path):
        data = {}
        try:
            with open(path, encoding='utf-8') as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, _, value = line.partition('=')
                        data[key.strip()] = value.strip()
        except OSError:
            pass
        return data

    def prompt_bool(self, label, default=True):
        default_str = 's' if default else 'n'
        ans = self.prompt(f'{label} (s/n)', default_str).strip().lower()
        if ans in ('', default_str):
            return default
        return ans == 's'

    def handle(self, *args, **options):
        env_path = settings.BASE_DIR / '.env'
        self.existing = {}
        if env_path.exists():
            self.existing = self._load_env(env_path)

        if options['production']:
            production = True
            interactive = False
        elif options['development']:
            production = False
            interactive = False
        else:
            default_env = '1' if self.existing.get('DEBUG') == 'False' else '2'
            choice = self.prompt('¿Entorno? (1) Producción   (2) Desarrollo', default_env)
            production = choice.strip() == '1'
            interactive = True

        # Si ya existe .env, en modo interactivo PREGUNTAMOS antes de sobrescribir
        # (default NO para no cargarse un .env afinado a mano). En no-interactivo
        # se regenera usando los valores actuales como defaults.
        if env_path.exists() and interactive:
            regenerate = self.prompt_bool(
                'El archivo .env ya existe. ¿Regenerarlo? (se perderán cambios manuales)',
                default=False,
            )
            if not regenerate:
                self.stdout.write(
                    self.style.WARNING('ℹ️ Manteniendo .env existente. No se sobrescribe.')
                )
                return

        # Rotación de claves: por defecto se conservan (no invalidar sesiones).
        # Si están comprometidas, rotar (prompt interactivo o --rotate-keys).
        rotate_keys = bool(options.get('rotate_keys'))
        has_keys = bool(self.existing.get('SECRET_KEY') and self.existing.get('ENCRYPTION_KEY'))
        if interactive and has_keys:
            rotate_keys = self.prompt_bool(
                '¿Rotar (regenerar) SECRET_KEY/ENCRYPTION_KEY? (solo si estan comprometidos)',
                default=False,
            )

        if has_keys and not rotate_keys:
            # Conservar claves existentes para no invalidar sesiones/cookies
            encrypted_secret_key = self.existing['SECRET_KEY']
            encryption_key = self.existing['ENCRYPTION_KEY']
        else:
            if rotate_keys:
                self.stdout.write(
                    self.style.WARNING(
                        '🔄 Rotando SECRET_KEY/ENCRYPTION_KEY. Sesiones y cookies '
                        'firmadas quedarán invalidadas (esperado al comprometerse).'
                    )
                )
            elif self.existing:
                self.stdout.write(
                    self.style.WARNING(
                        '⚠️ No se encontraron SECRET_KEY/ENCRYPTION_KEY válidos; se generan nuevos.'
                    )
                )
            secret_key = get_random_secret_key()
            encryption_key = Fernet.generate_key()
            encrypted_secret_key = Fernet(encryption_key).encrypt(secret_key.encode()).decode()
            encryption_key = encryption_key.decode()

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
                f.write(f'ENCRYPTION_KEY={encryption_key}\n\n')

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
        # Preguntar PRIMERO si se usará correo. Si no, no escribir nada.
        if interactive:
            use_email = self.prompt_bool('¿Configurar correo (email)?', default=not production)
        else:
            use_email = True
        if not use_email:
            f.write('# Correo desactivado (no se escriben variables de email).\n\n')
            return

        # Elegir backend: consola (solo dev) o servidor real (SMTP).
        if interactive and not production:
            self.stdout.write('Backend de correo:')
            self.stdout.write('  1. Consola (no requiere servidor; solo desarrollo)')
            self.stdout.write('  2. Servidor real (SMTP)')
            choice = self.prompt('Seleccione', '1')
            backend_console = choice.strip() == '1'
        else:
            backend_console = False  # producción exige servidor real

        if backend_console:
            f.write('EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend\n\n')
            return

        # Servidor real
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

        backend = (
            CUSTOM_EMAIL_BACKEND if autofirmado else 'django.core.mail.backends.smtp.EmailBackend'
        )
        f.write(f'EMAIL_BACKEND={backend}\n')
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
        if interactive:
            if production:
                options = [('postgresql', 'PostgreSQL'), ('mysql', 'MySQL')]
            else:
                options = [
                    ('sqlite3', 'SQLite (archivo local)'),
                    ('postgresql', 'PostgreSQL'),
                    ('mysql', 'MySQL'),
                ]
            self.stdout.write('Motor de base de datos:')
            for i, (_val, desc) in enumerate(options, 1):
                self.stdout.write(f'  {i}. {desc}')
            existing_engine = self.existing.get(
                'DB_ENGINE', 'postgresql' if production else 'sqlite3'
            )
            default_idx = next(
                (i for i, (v, _) in enumerate(options, 1) if v == existing_engine), 1
            )
            choice = self.prompt('Seleccione motor (número)', str(default_idx))
            try:
                idx = int(choice) - 1
                engine = options[idx][0]
            except (ValueError, IndexError):
                engine = options[0][0]
        else:
            engine = 'postgresql' if production else 'sqlite3'

        if engine == 'sqlite3':
            f.write('DB_ENGINE=sqlite3\n\n')
            return

        if interactive:
            name = self.prompt('DB_NAME', 'web_db')
            user = self.prompt('DB_USER', 'postgres')
            db_cred = self.prompt('DB_PASS', 'contraseña_segura', secret=True)
            host = self.prompt('DB_HOST', 'localhost')
            port = self.prompt('DB_PORT', '5432' if engine == 'postgresql' else '3306')
        else:
            name = 'web_db'
            user = 'postgres'
            db_cred = 'contraseña_segura'
            host = 'localhost'
            port = '5432' if engine == 'postgresql' else '3306'
        f.write(f'DB_ENGINE={engine}\n')
        f.write(f'DB_NAME={name}\n')
        f.write(f'DB_USER={user}\n')
        f.write(f'DB_PASS={db_cred}\n')
        f.write(f'DB_HOST={host}\n')
        f.write(f'DB_PORT={port}\n')
        f.write('DB_SSL_MODE=prefer\n\n')

    def _write_ldap_config(self, f, production, interactive):
        f.write('# =====================\n')
        f.write('# CONFIGURACIÓN LDAP (OPCIONAL)\n')
        f.write('# =====================\n')
        # Preguntar PRIMERO si se usará LDAP. Si no, no escribir nada.
        usar_ldap = self.prompt_bool('¿Configurar LDAP?', default=False) if interactive else False
        if not usar_ldap:
            f.write('# LDAP desactivado (no se escriben variables de LDAP).\n\n')
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
        f.write('LDAP_USER_ATTR_MAP=first_name:givenName,last_name:sn,email:mail\n')
        f.write('LDAP_CACHE_TIMEOUT=3600\n\n')
