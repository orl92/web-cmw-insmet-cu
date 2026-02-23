from dashboard.models import ServiceSubscription
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def create_clientes_group(sender, **kwargs):
    if sender.name == 'accounts':
        group, _ = Group.objects.get_or_create(name='Clientes')
        content_type = ContentType.objects.get_for_model(ServiceSubscription)
        
        # Crear el permiso si no existe (con el nombre exacto del modelo)
        view_perm, _ = Permission.objects.get_or_create(
            content_type=content_type,
            codename='view_subscription',
            defaults={'name': 'Ver'}
        )
        
        # Añadir el permiso al grupo si aún no lo tiene
        if view_perm not in group.permissions.all():
            group.permissions.add(view_perm)
            print("✓ Permiso 'view_subscription' añadido al grupo 'Clientes'")
