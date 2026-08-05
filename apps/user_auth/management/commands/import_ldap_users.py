import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from ldap3 import ALL, SUBTREE, Connection, Server
from ldap3.core.exceptions import LDAPException


class Command(BaseCommand):
    help = 'Importa usuarios de LDAP que tengan email, nombre y apellido completos usando ldap3'

    def handle(self, *args, **options):
        user_model = get_user_model()

        # Configuración desde variables de entorno
        server_uri = os.getenv('LDAP_SERVER_URI')
        bind_dn = os.getenv('LDAP_BIND_DN')
        bind_password = os.getenv('LDAP_BIND_PASSWORD')
        search_base = os.getenv('LDAP_USER_SEARCH_BASE', 'OU=CMW,DC=cmw,DC=insmet,DC=cu')
        search_filter = '(&(objectClass=user)(mail=*)(givenName=*)(sn=*))'
        attributes = ['sAMAccountName', 'givenName', 'sn', 'mail']

        if not server_uri or not bind_dn or not bind_password:
            self.stdout.write(
                self.style.ERROR('Faltan variables de entorno necesarias para la conexión LDAP')
            )
            return

        try:
            server = Server(server_uri, get_info=ALL)
            conn = Connection(server, user=bind_dn, password=bind_password, auto_bind=True)

            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=attributes,
            )

            total = 0
            imported = 0

            for entry in conn.entries:
                total += 1
                try:
                    username = str(entry.sAMAccountName)
                    first_name = str(entry.givenName).strip()
                    last_name = str(entry.sn).strip()
                    email = str(entry.mail).strip()

                    if not all([username, first_name, last_name, email]):
                        self.stdout.write(
                            self.style.WARNING(
                                f'Usuario {username} omitido - faltan datos requeridos'
                            )
                        )
                        continue

                    user, created = user_model.objects.get_or_create(username=username)
                    user.first_name = first_name
                    user.last_name = last_name
                    user.email = email
                    user.is_active = True
                    user.save()

                    imported += 1
                    action = 'Creado' if created else 'Actualizado'
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'{action}: {username} - {first_name} {last_name} <{email}>'
                        )
                    )

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error procesando entrada LDAP: {str(e)}'))

            self.stdout.write(
                self.style.SUCCESS(
                    f'\nProceso completado. {imported} de {total} usuarios importados/actualizados'
                )
            )

        except LDAPException as e:
            self.stdout.write(self.style.ERROR(f'Error de conexión LDAP: {str(e)}'))
