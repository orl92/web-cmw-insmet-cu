import os
import sys
from pathlib import Path

from cryptography.fernet import Fernet
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key


class Command(BaseCommand):
    help = 'Genera archivo .env con valores iniciales por defecto'

    def add_arguments(self, parser):
        parser.add_argument(
            '--production',
            action='store_true',
            help='Generar configuración para producción'
        )

    def handle(self, *args, **options):
        production = options['production']
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        env_path = base_dir / '.env'

        if env_path.exists():
            self.stdout.write(self.style.WARNING("El archivo .env ya existe. No se sobrescribirá."))
            return

        secret_key = get_random_secret_key()
        encryption_key = Fernet.generate_key()
        cipher_suite = Fernet(encryption_key)
        encrypted_secret_key = cipher_suite.encrypt(secret_key.encode()).decode()

        try:
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write("# =====================\n")
                f.write("# CONFIGURACIÓN BÁSICA (REQUERIDA)\n")
                f.write("# =====================\n")
                f.write(f"DEBUG={'False' if production else 'True'}\n")
                f.write(f"SECRET_KEY={encrypted_secret_key}\n")
                f.write(f"ENCRYPTION_KEY={encryption_key.decode()}\n\n")

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
                    f.write("# CUSTOM_EMAIL_BACKEND=config.custom_email_backend.CustomSTARTTLSBackend\n")
                    f.write("# EMAIL_USE_SSL=False\n\n")

                if production:
                    f.write("# =====================\n")
                    f.write("# CONFIGURACIÓN DE DOMINIO (PRODUCCIÓN - ⚠️ MODIFICAR! ⚠️)\n")
                    f.write("# =====================\n")
                    f.write("# Ejemplo: tu-dominio.com (sin http://)\n")
                    f.write("EXTERNAL_HOSTNAME=cmw.insmet.cu\n\n")
                    f.write("# Opcional: Puede definir manualmente estos valores si necesita configuraciones especiales\n")
                    f.write("# ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com\n")
                    f.write("# CSRF_TRUSTED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com\n\n")

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
                    f.write("CUSTOM_EMAIL_BACKEND=config.custom_email_backend.CustomSTARTTLSBackend\n")
                    f.write("EMAIL_USE_SSL=False\n")

                    f.write("# =====================\n")
                    f.write("# BASE DE DATOS (PRODUCCIÓN - ⚠️ MODIFICAR!)\n")
                    f.write("# =====================\n")
                    f.write("DB_ENGINE=postgresql\n")
                    f.write("DB_NAME=web_db\n")
                    f.write("DB_USER=postgres\n")
                    f.write("DB_PASS=contraseña_segura\n")
                    f.write("DB_HOST=localhost\n")
                    f.write("DB_PORT=5432\n")
                    f.write("DB_SSL_MODE=prefer\n")
                    f.write("# DB_SSL_ROOT_CERT=/ruta/ca.crt\n\n")

                    f.write("# =====================\n")
                    f.write("# CONFIGURACIÓN LDAP\n")
                    f.write("# =====================\n")
                    f.write("# --- OpenLDAP (Linux) ---\n")
                    f.write("LDAP_SERVER_URI=ldap://dc.cmw.insmet.cu:389\n")
                    f.write("LDAP_START_TLS=True\n")
                    f.write("LDAP_BIND_DN=CN=linux,CN=Users,DC=cmw,DC=insmet,DC=cu\n")
                    f.write("LDAP_BIND_PASSWORD=tu_contraseña_ldap\n")
                    f.write("LDAP_USER_SEARCH_BASE=OU=CMW,DC=cmw,DC=insmet,DC=cu\n")
                    f.write("LDAP_GROUP_SEARCH_BASE=OU=CMW,DC=cmw,DC=insmet,DC=cu\n")
                    f.write("LDAP_STAFF_GROUP=cn=staff,OU=CMW,DC=cmw,DC=insmet,DC=cu\n")
                    f.write("LDAP_SUPERUSER_GROUP=cn=superuser,OU=CMW,DC=cmw,DC=insmet,DC=cu\n")
                    f.write("# LDAP_USER_ATTR_MAP=first_name:givenName,last_name:sn,email:mail\n")
                    f.write("# LDAP_CACHE_TIMEOUT=3600\n\n")

                else:
                    f.write("ALLOWED_HOSTS=localhost,127.0.0.1\n")
                    f.write("CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000\n\n")
                    f.write("# EXTERNAL_HOSTNAME=cmw.insmet.cu\n\n")

            self.stdout.write(self.style.SUCCESS("✅ Archivo .env creado exitosamente"))
            self.stdout.write("🔑 SECRET_KEY generada automáticamente.")

            if production:
                self.stdout.write(self.style.WARNING("\n⚠️ ATENCIÓN: Debe editar manualmente estas variables CRÍTICAS:"))
                self.stdout.write("  - EXTERNAL_HOSTNAME (debe ser su dominio real sin http://)")
                self.stdout.write("  - Configuración LDAP (servidor, credenciales y bases de búsqueda)")
                self.stdout.write("\n💡 El sistema generará automáticamente:")
                self.stdout.write("  - ALLOWED_HOSTS basado en EXTERNAL_HOSTNAME")
                self.stdout.write("  - CSRF_TRUSTED_ORIGINS (con https://)")
                self.stdout.write("\n💡 RECOMENDACIONES:")
                self.stdout.write("  - Use PostgreSQL o MySQL como motor de base de datos")
                self.stdout.write("  - Configure backups automáticos de la base de datos")
                self.stdout.write("  - Revise los permisos de los archivos sensibles")
                self.stdout.write("  - Para LDAP, use cuentas con permisos mínimos necesarios")

            self.stdout.write("\n✏️ Puede editarlo con cualquier editor de texto.")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error al crear .env: {e}"))
            self.stdout.write("ℹ️ Verifique los permisos de escritura en el directorio")
            sys.exit(1)
