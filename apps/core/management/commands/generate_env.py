import sys
from datetime import datetime

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key


class Command(BaseCommand):
    help = 'Genera archivo .env con valores iniciales por defecto'

    def add_arguments(self, parser):
        parser.add_argument(
            '--production', action='store_true', help='Generar configuración para producción'
        )

    def handle(self, *args, **options):
        # ============================================================
        # 📂 PASO 1: Obtener ruta y verificar si .env ya existe
        # ============================================================
        production = options['production']
        env_path = settings.BASE_DIR / '.env'

        if env_path.exists():
            self.stdout.write(
                self.style.WARNING('⚠️ El archivo .env ya existe. No se sobrescribirá.')
            )
            return

        # ============================================================
        # 🔐 PASO 2: Generar claves
        # ============================================================
        secret_key = get_random_secret_key()
        encryption_key = Fernet.generate_key()
        cipher_suite = Fernet(encryption_key)
        encrypted_secret_key = cipher_suite.encrypt(secret_key.encode()).decode()

        # ============================================================
        # 📝 PASO 3: Escribir el archivo .env
        # ============================================================
        try:
            with open(env_path, 'w', encoding='utf-8') as f:
                # --- Cabecera ---
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

                # --- Configuración de producción ---
                if production:
                    self._write_production_config(f)
                else:
                    self._write_development_config(f)

                # --- Configuración de email ---
                self._write_email_config(f, production)

                # --- Configuración de base de datos ---
                self._write_database_config(f, production)

                # --- Configuración LDAP ---
                self._write_ldap_config(f, production)

                # --- Configuración CORS ---
                f.write('# =====================\n')
                f.write('# CONFIGURACIÓN CORS\n')
                f.write('# =====================\n')
                if production:
                    f.write(
                        'CORS_ALLOWED_ORIGINS=https://cmw.insmet.cu,https://www.cmw.insmet.cu\n\n'
                    )
                else:
                    f.write('CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000\n\n')

                # --- Configuración de logging ---
                f.write('# =====================\n')
                f.write('# CONFIGURACIÓN DE LOGGING\n')
                f.write('# =====================\n')
                f.write('LOG_LEVEL=INFO\n')
                f.write('LOG_FILE=/var/log/cmw/app.log\n\n')

                # --- Configuración de cache ---
                f.write('# =====================\n')
                f.write('# CONFIGURACIÓN DE CACHE\n')
                f.write('# =====================\n')
                f.write('# CACHE_BACKEND=django.core.cache.backends.redis.RedisCache\n')
                f.write('# CACHE_LOCATION=redis://localhost:6379/1\n')
                f.write('CACHE_BACKEND=django.core.cache.backends.locmem.LocMemCache\n\n')

            # ============================================================
            # ✅ PASO 4: Mostrar mensajes de éxito
            # ============================================================
            self.stdout.write(self.style.SUCCESS('✅ Archivo .env creado exitosamente'))
            self.stdout.write(f'📁 Ubicación: {env_path}')
            self.stdout.write('🔑 SECRET_KEY y ENCRYPTION_KEY generadas automáticamente.')

            if production:
                self.stdout.write(
                    self.style.WARNING(
                        '\n⚠️ ATENCIÓN: Debe editar manualmente estas variables CRÍTICAS:'
                    )
                )
                self.stdout.write('  • EXTERNAL_HOSTNAME (debe ser su dominio real sin http://)')
                self.stdout.write(
                    '  • Configuración LDAP (servidor, credenciales y bases de búsqueda)'
                )
                self.stdout.write('  • Configuración de email (servidor SMTP real)')
                self.stdout.write('  • Configuración de base de datos (usuario, contraseña, host)')
                self.stdout.write('\n💡 RECOMENDACIONES:')
                self.stdout.write('  • Use PostgreSQL o MySQL como motor de base de datos')
                self.stdout.write('  • Configure backups automáticos de la base de datos')
                self.stdout.write('  • Revise los permisos de los archivos sensibles (.env)')
                self.stdout.write('  • Para LDAP, use cuentas con permisos mínimos necesarios')

            self.stdout.write('\n✏️ Puede editarlo con cualquier editor de texto:')
            self.stdout.write(f'  nano {env_path}')
            self.stdout.write(f'  vim {env_path}')
            self.stdout.write(f'  code {env_path}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error al crear .env: {e}'))
            self.stdout.write('ℹ️ Verifique los permisos de escritura en el directorio')
            sys.exit(1)

    # ============================================================
    # 📌 MÉTODOS AUXILIARES
    # ============================================================

    def _write_development_config(self, f):
        """Escribe configuración para desarrollo"""
        f.write('# =====================\n')
        f.write('# CONFIGURACIÓN DE DOMINIO (DESARROLLO)\n')
        f.write('# =====================\n')
        f.write('ALLOWED_HOSTS=localhost,127.0.0.1\n')
        f.write('CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000\n')
        f.write('# EXTERNAL_HOSTNAME=cmw.insmet.cu\n\n')

    def _write_production_config(self, f):
        """Escribe configuración para producción"""
        f.write('# =====================\n')
        f.write('# CONFIGURACIÓN DE DOMINIO (PRODUCCIÓN - ⚠️ MODIFICAR! ⚠️)\n')
        f.write('# =====================\n')
        f.write('# Ejemplo: tu-dominio.com (sin http://)\n')
        f.write('EXTERNAL_HOSTNAME=cmw.insmet.cu\n\n')
        f.write(
            '# Opcional: Puede definir manualmente estos valores si necesita '
            'configuraciones especiales\n'
        )
        f.write('# ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com\n')
        f.write('# CSRF_TRUSTED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com\n\n')

    def _write_email_config(self, f, production):
        """Escribe configuración de email"""
        f.write('# =====================\n')
        f.write('# CONFIGURACIÓN DE EMAIL\n')
        f.write('# =====================\n')

        if production:
            f.write('# ⚠️ DEBE CONFIGURAR LOS VALORES REALES PARA PRODUCCIÓN ⚠️\n')
            f.write('EMAIL_USE_TLS=True\n')
            f.write('EMAIL_HOST=smtp.tu-dominio.com\n')
            f.write('EMAIL_PORT=587\n')
            f.write('EMAIL_HOST_USER=user@tu-dominio.com\n')
            f.write('EMAIL_HOST_PASSWORD=tu_contraseña_segura\n')
            f.write("DEFAULT_FROM_EMAIL='Centro Meteorológico Camagüey <user@tu-dominio.com>'\n")
            f.write('CUSTOM_EMAIL_BACKEND=config.custom_email_backend.CustomSTARTTLSBackend\n')
            f.write('EMAIL_USE_SSL=False\n\n')
        else:
            f.write('# Configuración para desarrollo (usa consola)\n')
            f.write('EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend\n')
            f.write('# Descomenta el resto para usar servidor SMTP real\n\n')
            f.write('# EMAIL_USE_TLS=True\n')
            f.write('# EMAIL_HOST=smtp.tu-dominio.com\n')
            f.write('# EMAIL_PORT=587\n')
            f.write('# EMAIL_HOST_USER=user@tu-dominio.com\n')
            f.write('# EMAIL_HOST_PASSWORD=tu_contraseña_segura\n')
            f.write("# DEFAULT_FROM_EMAIL='Centro Meteorológico Camagüey <user@tu-dominio.com>'\n")
            f.write('# CUSTOM_EMAIL_BACKEND=config.custom_email_backend.CustomSTARTTLSBackend\n')
            f.write('# EMAIL_USE_SSL=False\n\n')

    def _write_database_config(self, f, production):
        """Escribe configuración de base de datos"""
        f.write('# =====================\n')
        f.write('# CONFIGURACIÓN DE BASE DE DATOS\n')
        f.write('# =====================\n')

        if production:
            f.write('# ⚠️ DEBE CONFIGURAR LOS VALORES REALES PARA PRODUCCIÓN ⚠️\n')
            f.write('DB_ENGINE=postgresql\n')
            f.write('DB_NAME=web_db\n')
            f.write('DB_USER=postgres\n')
            f.write('DB_PASS=contraseña_segura\n')
            f.write('DB_HOST=localhost\n')
            f.write('DB_PORT=5432\n')
            f.write('DB_SSL_MODE=prefer\n')
            f.write('# DB_SSL_ROOT_CERT=/ruta/ca.crt\n\n')
        else:
            f.write('# Desarrollo usa SQLite por defecto\n')
            f.write('DB_ENGINE=sqlite3\n')
            f.write('# Para usar PostgreSQL descomentar:\n')
            f.write('# DB_ENGINE=postgresql\n')
            f.write('# DB_NAME=web_db_dev\n')
            f.write('# DB_USER=postgres\n')
            f.write('# DB_PASS=postgres\n')
            f.write('# DB_HOST=localhost\n')
            f.write('# DB_PORT=5432\n\n')

    def _write_ldap_config(self, f, production):
        """Escribe configuración LDAP"""
        f.write('# =====================\n')
        f.write('# CONFIGURACIÓN LDAP (OPCIONAL)\n')
        f.write('# =====================\n')

        if production:
            f.write('# --- OpenLDAP (Linux) - ⚠️ MODIFICAR! ⚠️ ---\n')
            f.write('LDAP_SERVER_URI=ldap://dc.cmw.insmet.cu:389\n')
            f.write('LDAP_START_TLS=True\n')
            f.write('LDAP_BIND_DN=CN=linux,CN=Users,DC=cmw,DC=insmet,DC=cu\n')
            f.write('LDAP_BIND_PASSWORD=tu_contraseña_ldap\n')
            f.write('LDAP_USER_SEARCH_BASE=OU=CMW,DC=cmw,DC=insmet,DC=cu\n')
            f.write('LDAP_GROUP_SEARCH_BASE=OU=CMW,DC=cmw,DC=insmet,DC=cu\n')
            f.write('LDAP_STAFF_GROUP=cn=staff,OU=CMW,DC=cmw,DC=insmet,DC=cu\n')
            f.write('LDAP_SUPERUSER_GROUP=cn=superuser,OU=CMW,DC=cmw,DC=insmet,DC=cu\n')
            f.write('# LDAP_USER_ATTR_MAP=first_name:givenName,last_name:sn,email:mail\n')
            f.write('# LDAP_CACHE_TIMEOUT=3600\n\n')
        else:
            f.write('# LDAP desactivado por defecto en desarrollo\n')
            f.write('# Para activar descomentar:\n')
            f.write('# LDAP_SERVER_URI=ldap://localhost:389\n')
            f.write('# LDAP_START_TLS=False\n')
            f.write('# LDAP_BIND_DN=cn=admin,dc=example,dc=org\n')
            f.write('# LDAP_BIND_PASSWORD=admin\n')
            f.write('# LDAP_USER_SEARCH_BASE=ou=users,dc=example,dc=org\n')
            f.write('# LDAP_GROUP_SEARCH_BASE=ou=groups,dc=example,dc=org\n')
            f.write('# LDAP_STAFF_GROUP=cn=staff,ou=groups,dc=example,dc=org\n')
            f.write('# LDAP_SUPERUSER_GROUP=cn=superuser,ou=groups,dc=example,dc=org\n\n')
