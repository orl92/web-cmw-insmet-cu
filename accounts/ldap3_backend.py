import os
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
import ldap3
from ldap3.core.exceptions import LDAPException

logger = logging.getLogger(__name__)

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1") if isinstance(v, str) else v

class LDAP3Backend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Si no se proporciona contraseña, no intentar autenticación LDAP
        if password is None or password == '':
            return None

        # Obtener configuración desde variables de entorno
        server_uri = os.getenv('LDAP_SERVER_URI')
        start_tls = str2bool(os.getenv('LDAP_START_TLS', 'True'))
        bind_dn = os.getenv('LDAP_BIND_DN')
        bind_password = os.getenv('LDAP_BIND_PASSWORD')
        user_search_base = os.getenv('LDAP_USER_SEARCH_BASE')
        group_search_base = os.getenv('LDAP_GROUP_SEARCH_BASE')
        staff_group = os.getenv('LDAP_STAFF_GROUP')
        superuser_group = os.getenv('LDAP_SUPERUSER_GROUP')
        
        if not server_uri:
            logger.error("LDAP_SERVER_URI no configurado")
            return None

        try:
            # Configurar conexión LDAP
            server = ldap3.Server(server_uri, get_info=ldap3.ALL)
            
            # Conectar con credenciales de búsqueda
            conn = ldap3.Connection(
                server, 
                user=bind_dn, 
                password=bind_password,
                auto_bind=True
            )
            
            # Iniciar TLS si es necesario
            if start_tls:
                conn.start_tls()
            
            # Buscar usuario
            user_filter = f"(sAMAccountName={username})"
            conn.search(
                search_base=user_search_base,
                search_filter=user_filter,
                search_scope=ldap3.SUBTREE,
                attributes=['*']
            )
            
            if not conn.entries:
                logger.warning(f"Usuario no encontrado en LDAP: {username}")
                return None
                
            user_entry = conn.entries[0]
            user_dn = user_entry.entry_dn
            
            # Autenticar con credenciales del usuario
            user_conn = ldap3.Connection(
                server, 
                user=user_dn, 
                password=password,
                auto_bind=True
            )
            
            # Si la autenticación es exitosa, obtener o crear el usuario en Django
            return self.get_or_create_user(
                username, 
                user_entry, 
                group_search_base,
                staff_group,
                superuser_group,
                conn
            )
            
        except LDAPException as e:
            logger.error(f"Error de LDAP: {str(e)}")
            return None
        except Exception as e:
            logger.exception(f"Error inesperado durante autenticación LDAP")
            return None
    
    def get_or_create_user(self, username, user_entry, group_search_base, 
                          staff_group, superuser_group, conn):
        User = get_user_model()
        user_attrs = self.get_user_attributes(user_entry)
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User(username=username)
            user.set_unusable_password()  # No almacenar contraseña en Django
        
        # Actualizar atributos del usuario
        for field, value in user_attrs.items():
            if hasattr(user, field) and value:
                setattr(user, field, value)
        
        # Verificar pertenencia a grupos
        if group_search_base:
            user.is_staff = self.is_member_of(conn, user_entry, staff_group, group_search_base)
            user.is_superuser = self.is_member_of(conn, user_entry, superuser_group, group_search_base)
        
        user.save()
        return user
    
    def get_user_attributes(self, user_entry):
        # Mapear atributos LDAP a campos de usuario Django
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
            return False
        
        # Buscar si el usuario pertenece al grupo
        try:
            user_dn = user_entry.entry_dn
            conn.search(
                search_base=group_search_base,
                search_filter=f"(&(distinguishedName={group_dn})(member={user_dn}))",
                search_scope=ldap3.SUBTREE,
                attributes=['dn']
            )
            return bool(conn.entries)
        except LDAPException:
            return False
    
    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except ObjectDoesNotExist:
            return None