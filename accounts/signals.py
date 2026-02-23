from dashboard.models import ServiceSubscription
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def create_clientes_group(sender, **kwargs):
    if sender.name == 'accounts':
        group, created = Group.objects.get_or_create(name='Clientes')
        
        if created:
            # Asignar permisos básicos para Clientes
            content_type = ContentType.objects.get_for_model(ServiceSubscription)
            
            try:
                view_perm = Permission.objects.get(
                    content_type=content_type,
                    codename='view_subscription'
                )
                group.permissions.add(view_perm)
                print("✓ Grupo 'Clientes' creado con permiso para ver suscripciones")
            except Permission.DoesNotExist:
                print("⚠ Permiso 'view_subscription' no encontrado")
