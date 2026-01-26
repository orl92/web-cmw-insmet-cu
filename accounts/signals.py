from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from dashboard.models import Service


@receiver(post_migrate)
def create_clientes_group(sender, **kwargs):
    # Crear grupo "clientes" automáticamente al hacer migraciones
    if sender.name == 'accounts':
        group, created = Group.objects.get_or_create(name='clientes')
        
        if created:
            # Asignar permisos básicos para clientes
            # Solo permiso para ver servicios
            service_content_type = ContentType.objects.get_for_model(Service)
            
            try:
                view_service_perm = Permission.objects.get(
                    content_type=service_content_type,
                    codename='view_service'
                )
                group.permissions.add(view_service_perm)
                print("✓ Grupo 'clientes' creado con permiso para ver servicios")
            except Permission.DoesNotExist:
                print("⚠ Permiso 'view_service' no encontrado")
