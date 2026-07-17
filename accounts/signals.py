from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate, post_save, pre_delete
from django.dispatch import receiver

from dashboard.models import ServiceSubscription, EmailRecipient, EmailRecipientList


def _sync_newsletter_recipient(profile):
    if not profile.user.email:
        return
    newsletter_list, _ = EmailRecipientList.objects.get_or_create(
        name='Newsletter',
        defaults={'description': 'Usuarios que desean recibir novedades por correo.'}
    )
    if profile.newsletter:
        EmailRecipient.objects.get_or_create(
            email=profile.user.email,
            recipient_list=newsletter_list
        )
    else:
        EmailRecipient.objects.filter(
            email=profile.user.email,
            recipient_list=newsletter_list
        ).delete()


@receiver(post_save, sender='accounts.Profile')
def sync_profile_newsletter(sender, instance, **kwargs):
    _sync_newsletter_recipient(instance)


@receiver(pre_delete, sender='accounts.Profile')
def cleanup_newsletter_on_delete(sender, instance, **kwargs):
    if instance.newsletter and instance.user.email:
        newsletter_list = EmailRecipientList.objects.filter(name='Newsletter').first()
        if newsletter_list:
            EmailRecipient.objects.filter(
                email=instance.user.email,
                recipient_list=newsletter_list
            ).delete()


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
