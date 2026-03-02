import logging
import os
import uuid

from common.utils import FileHandlerMixin, image_upload_path
from core import settings
from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image

logger = logging.getLogger(__name__)

# Create your models here.

class Profile(FileHandlerMixin, models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(
        null=True, blank=True,
        upload_to=image_upload_path
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_ldap = models.BooleanField(default=False)

    # Lista de campos de archivo para que el mixin los gestione
    file_fields = ['avatar']

    def save(self, *args, **kwargs):
        # Primero guardamos para tener el archivo en disco
        super().save(*args, **kwargs)

        # Redimensionar y recortar imagen (solo si hay avatar)
        if self.avatar and os.path.exists(self.avatar.path):
            # Redimensionar manteniendo proporción
            with Image.open(self.avatar.path) as img:
                wide, high = img.size
                if wide > high:
                    new_high = 300
                    new_wide = int((wide / high) * new_high)
                    img = img.resize((new_wide, new_high))
                elif high > wide:
                    new_wide = 300
                    new_high = int((high / wide) * new_wide)
                    img = img.resize((new_wide, new_high))
                else:
                    img.thumbnail((300, 300))
                img.save(self.avatar.path)

            # Recorte cuadrado
            with Image.open(self.avatar.path) as img:
                wide, high = img.size
                if wide > high:
                    left = (wide - high) / 2
                    top = 0
                    right = (wide + high) / 2
                    bottom = high
                else:
                    left = 0
                    top = (high - wide) / 2
                    right = wide
                    bottom = (high + wide) / 2
                img = img.crop((left, top, right, bottom))
                img.save(self.avatar.path)


    def get_avatar(self):
        if self.avatar:
            return f'{settings.MEDIA_URL}{self.avatar}'
        return f'{settings.STATIC_URL}dist/img/avatar.png'

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'
        default_permissions = ()
        permissions = (
            ('view_profile', 'Ver'),
            ('add_profile', 'Añadir'),
            ('change_profile', 'Editar'),
            ('delete_profile', 'Eliminar'),
        )

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crea un perfil SOLO para usuarios no-LDAP
    """
    if created:
        # Verificar si el usuario se está creando a través de LDAP
        if not hasattr(instance, '_is_ldap_user'):
            Profile.objects.create(user=instance, is_ldap=False)
            logger.debug(f"Señal: Perfil no-LDAP creado para {instance.username}")

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Guarda el perfil solo para usuarios no LDAP
    """
    # Ignorar usuarios LDAP
    if hasattr(instance, '_is_ldap_user'):
        return
        
    if hasattr(instance, 'profile') and not instance.profile.is_ldap:
        instance.profile.save()

class GroupProfile(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return self.group.name
    
    class Meta:
        verbose_name = 'Perfil Grupo'
        verbose_name_plural = 'Perfiles Grupos'
        default_permissions = ()
        permissions = (
            ('view_group', 'Ver'),
            ('add_group', 'Añadir'),
            ('change_group', 'Editar'),
            ('delete_group', 'Eliminar'),
        )

@receiver(post_save, sender=Group)
def create_group_profile(sender, instance, created, **kwargs):
    if created:
        GroupProfile.objects.create(group=instance)

@receiver(post_save, sender=Group)
def save_group_profile(sender, instance, **kwargs):
    if not instance._state.adding:
        instance.groupprofile.save()