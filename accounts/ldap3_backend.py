import os
import logging
import ldap3
from ldap3.core.exceptions import LDAPException
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import ObjectDoesNotExist
from accounts.models import Profile

logger = logging.getLogger(__name__)

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1") if isinstance(v, str) else v

class LDAP3Backend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        logger.debug(f"🔑 Iniciando autenticación LDAP para: {username}")
        if password is None or password == '':
            logger.debug("🔑 Contraseña vacía, abortando autenticación LDAP.")
            return None

        server_uri = os.getenv('LDAP_SERVER_URI')
        start_tls = str2bool(os.getenv('LDAP_START_TLS', 'True'))
        bind_dn = os.getenv('LDAP_BIND_DN')
        bind_password = os.getenv('LDAP_BIND_PASSWORD')
        user_search_base = os.getenv('LDAP_USER_SEARCH_BASE')
        group_search_base = os.getenv('LDAP_GROUP_SEARCH_BASE')
        staff_group = os.getenv('LDAP_STAFF_GROUP')
        superuser_group = os.getenv('LDAP_SUPERUSER_GROUP')

        if not server_uri:
            logger.error("❌ LDAP_SERVER_URI no configurado")
            return None

        try:
            # Configurar conexión LDAP
            server = ldap3.Server(server_uri, get_info=ldap3.ALL)
            conn = ldap3.Connection(server, user=bind_dn, password=bind_password, auto_bind=True)

            if start_tls:
                conn.start_tls()

            user_filter = f"(sAMAccountName={username})"
            
            conn.search(
                search_base=user_search_base,
                search_filter=user_filter,
                search_scope=ldap3.SUBTREE,
                attributes=['*']
            )

            if not conn.entries:
                logger.warning(f"⚠️ Usuario no encontrado en LDAP: {username}")
                return None

            user_entry = conn.entries[0]
            user_dn = user_entry.entry_dn

            # Validar credenciales del usuario
            user_conn = ldap3.Connection(server, user=user_dn, password=password, auto_bind=True)

            # Crear/actualizar usuario y perfil
            user = self.get_or_create_user(
                username,
                user_entry,
                group_search_base,
                staff_group,
                superuser_group,
                conn
            )

            # Configurar backend para mantener la sesión
            user.backend = self.__module__ + '.' + self.__class__.__name__
            return user

        except LDAPException as e:
            logger.error(f"❌ Error de LDAP: {str(e)}")
            return None
        except Exception as e:
            logger.exception(f"❌ Error inesperado durante autenticación LDAP: {str(e)}")
            return None

    
    def get_or_create_user(self, username, user_entry, group_search_base, staff_group, superuser_group, conn):
        User = get_user_model()
        user_attrs = self.get_user_attributes(user_entry)

        try:
            user = User.objects.get(username=username)
            logger.debug(f"🔄 Usuario existente en Django: {username}")
            
            # =============================================================
            # ACTUALIZACIÓN DE USUARIO EXISTENTE
            # =============================================================
            changes = False
            
            # Actualizar campos básicos
            for field, value in user_attrs.items():
                current_value = getattr(user, field, None)
                if current_value != value and value is not None:
                    logger.debug(f"🔄 Actualizando campo {field} de '{current_value}' a '{value}'")
                    setattr(user, field, value)
                    changes = True
            
            # Actualizar permisos basados en grupos
            if group_search_base:
                new_staff = self.is_member_of(conn, user_entry, staff_group, group_search_base)
                new_superuser = self.is_member_of(conn, user_entry, superuser_group, group_search_base)
                
                if user.is_staff != new_staff:
                    user.is_staff = new_staff
                    changes = True
                    logger.debug(f"🔄 Actualizando is_staff a {new_staff}")
                
                if user.is_superuser != new_superuser:
                    user.is_superuser = new_superuser
                    changes = True
                    logger.debug(f"🔄 Actualizando is_superuser a {new_superuser}")
            
            # Guardar solo si hay cambios
            if changes:
                user.save()
                logger.info(f"💾 Usuario actualizado: {username}")
            else:
                logger.debug(f"✅ Usuario sin cambios: {username}")
            
            # =============================================================
            # ACTUALIZACIÓN DE PERFIL PARA USUARIOS EXISTENTES
            # =============================================================
            try:
                # Asegurarnos de tener el perfil
                profile, created = Profile.objects.get_or_create(
                    user=user, 
                    defaults={'is_ldap': True}
                )
                
                # Si el perfil ya existía pero no estaba marcado como LDAP
                if not created and not profile.is_ldap:
                    profile.is_ldap = True
                    profile.save()
                    logger.info(f"🔄 Perfil actualizado a is_ldap=True para {username}")
                
                logger.debug(f"🏁 Estado final is_ldap para {username}: {profile.is_ldap}")
                
            except Exception as e:
                logger.error(f"❌ Error al actualizar perfil para usuario existente: {str(e)}")
                # Forzar actualización si es necesario
                if hasattr(user, 'profile'):
                    user.profile.is_ldap = True
                    user.profile.save()
            
            return user
                
        except User.DoesNotExist:
            logger.debug(f"➕ Creando nuevo usuario: {username}")
            user = User(username=username)
            user.set_unusable_password()
            
            # Asignar atributos
            user.first_name = user_attrs.get("first_name", "")
            user.last_name = user_attrs.get("last_name", "")
            user.email = user_attrs.get("email", "")

            # Marcar como usuario LDAP (IMPORTANTE PARA LA SEÑAL)
            user._is_ldap_user = True

            # Verificar grupos
            if group_search_base:
                user.is_staff = self.is_member_of(conn, user_entry, staff_group, group_search_base)
                user.is_superuser = self.is_member_of(conn, user_entry, superuser_group, group_search_base)

            # Guardar usuario
            user.save()
            logger.info(f"✅ Nuevo usuario creado: {username}")

            # Crear perfil LDAP
            try:
                Profile.objects.create(user=user, is_ldap=True)
                logger.info(f"✅ Perfil LDAP creado para {username}")
            except Exception as e:
                logger.error(f"❌ Error al crear perfil LDAP: {str(e)}")
                Profile.objects.get_or_create(user=user, defaults={'is_ldap': True})
                logger.warning(f"⚠️ Perfil LDAP creado en modo fallback")
            
            # Verificacion de perfil
            try:
                # Asegurarnos de cargar la relación de perfil
                user.refresh_from_db()
                
                if hasattr(user, 'profile'):
                    if user.profile.is_ldap:
                        logger.debug(f"✔️ Confirmado: is_ldap=True para {username}")
                    else:
                        logger.error(f"❌ ERROR CRÍTICO: is_ldap=False para {username}")
                        # Forzar corrección
                        user.profile.is_ldap = True
                        user.profile.save()
                else:
                    # Crear perfil de emergencia
                    Profile.objects.create(user=user, is_ldap=True)
                    
            except Exception as e:
                logger.error(f"🚨 Error fatal en verificación de perfil: {str(e)}")
            
            return user
        
    def get_user_attributes(self, user_entry):
        return {
            "first_name": self.get_attr_value(user_entry, "givenName"),
            "last_name": self.get_attr_value(user_entry, "sn"),
            "email": self.get_attr_value(user_entry, "mail")
        }

    def get_attr_value(self, entry, attr_name):
        if hasattr(entry, attr_name):
            value = getattr(entry, attr_name).value
            return value[0] if isinstance(value, list) and value else value
        return None

    def is_member_of(self, conn, user_entry, group_dn, group_search_base):
        if not group_dn:
            logger.debug(f"👥 Grupo no configurado: {group_dn}")
            return False
        try:
            user_dn = user_entry.entry_dn
            conn.search(
                search_base=group_search_base,
                search_filter=f"(&(distinguishedName={group_dn})(member={user_dn}))",
                search_scope=ldap3.SUBTREE,
                attributes=['dn']
            )
            result = bool(conn.entries)
            return result
        except LDAPException as e:
            logger.error(f"❌ Error al verificar membresía en grupo {group_dn}: {str(e)}")
            return False

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except ObjectDoesNotExist:
            return None