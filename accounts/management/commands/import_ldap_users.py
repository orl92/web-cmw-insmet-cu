import ldap
from django.core.management.base import BaseCommand
from django_auth_ldap.backend import LDAPBackend
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Importa usuarios de LDAP que tengan email, nombre y apellido completos'

    def handle(self, *args, **options):
        User = get_user_model()
        ldap_backend = LDAPBackend()

        # Configuración de búsqueda
        search_base = 'OU=CMW,DC=cmw,DC=insmet,DC=cu'
        search_filter = '(&(objectClass=user)(mail=*)(givenName=*)(sn=*))'
        attrs = ['sAMAccountName', 'givenName', 'sn', 'mail']

        try:
            # Conectar a LDAP
            conn = ldap_backend.ldap.initialize(ldap_backend.settings.SERVER_URI)
            conn.simple_bind_s(ldap_backend.settings.BIND_DN, ldap_backend.settings.BIND_PASSWORD)

            # Buscar usuarios con los atributos requeridos
            results = conn.search_s(
                search_base,
                ldap.SCOPE_SUBTREE,
                search_filter,
                attrs
            )

            total = 0
            imported = 0

            for dn, entry in results:
                total += 1
                try:
                    username = entry['sAMAccountName'][0].decode('utf-8')
                    first_name = entry.get('givenName', [b''])[0].decode('utf-8').strip()
                    last_name = entry.get('sn', [b''])[0].decode('utf-8').strip()
                    email = entry.get('mail', [b''])[0].decode('utf-8').strip()

                    # Verificar que todos los campos tienen valores válidos
                    if not all([username, first_name, last_name, email]):
                        self.stdout.write(self.style.WARNING(
                            f'Usuario {username} omitido - faltan datos requeridos'
                        ))
                        continue

                    # Crear o actualizar usuario
                    user, created = User.objects.get_or_create(username=username)
                    user.first_name = first_name
                    user.last_name = last_name
                    user.email = email
                    user.is_active = True
                    user.save()

                    imported += 1
                    if created:
                        self.stdout.write(self.style.SUCCESS(
                            f'Creado: {username} - {first_name} {last_name} <{email}>'
                        ))
                    else:
                        self.stdout.write(self.style.SUCCESS(
                            f'Actualizado: {username} - {first_name} {last_name} <{email}>'
                        ))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'Error procesando entrada LDAP: {str(e)}'
                    ))

            self.stdout.write(self.style.SUCCESS(
                f'\nProceso completado. {imported} de {total} usuarios importados/actualizados'
            ))

        except ldap.LDAPError as e:
            self.stdout.write(self.style.ERROR(f'Error de conexión LDAP: {str(e)}'))