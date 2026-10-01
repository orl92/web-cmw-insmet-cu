import logging
import os
import uuid as uuid_lib

from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.templatetags.static import static
from PIL import Image

from apps.core.models import FileHandlerMixin, image_upload_path
from apps.core.validators import strict_pillow

logger = logging.getLogger(__name__)


class Profile(FileHandlerMixin, models.Model):
    file_fields = ['avatar']
    uuid = models.UUIDField(primary_key=True, default=uuid_lib.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(
        upload_to=image_upload_path, null=True, blank=True, verbose_name='Avatar'
    )
    is_ldap = models.BooleanField(default=False, verbose_name='Usuario LDAP')
    newsletter = models.BooleanField(default=False, verbose_name='Recibir boletín')

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'
        default_permissions = ()
        permissions = [
            ('view_profile', 'Ver perfiles'),
            ('add_profile', 'Añadir perfiles'),
            ('change_profile', 'Cambiar perfiles'),
            ('delete_profile', 'Eliminar perfiles'),
        ]

    def __str__(self):
        return self.user.username

    def get_avatar(self):
        if self.avatar:
            return self.avatar.url
        return static('dist/img/avatar.png')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._process_avatar()

    def _process_avatar(self):
        """Resize and crop the stored avatar in place, keeping it square.

        Pillow is forced to fully decode the file here, so a corrupted or
        truncated upload used to turn any save (form, admin, shell, signal)
        into an HTTP 500. Image processing is therefore best-effort: on
        failure the exception is logged and the stored file is left untouched
        instead of breaking the save.
        """
        if not self.avatar or not os.path.exists(self.avatar.path):
            return

        try:
            with strict_pillow():
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
        except Exception:
            # Deliberately broad, and deliberately so: this is the only thing
            # standing between a damaged file already sitting in storage and an
            # HTTP 500 on every later save. `PILLOW_ERRORS` is not enough here
            # because a few real failure modes are not OSError subclasses —
            # `zlib.error` on a broken IDAT stream, `struct.error` on a mangled
            # header — and a legacy file uploaded before validation existed can
            # still be on disk. Every failure is logged with a traceback, so a
            # genuine programming bug here stays visible instead of silent.
            logger.exception(
                'No se pudo procesar el avatar del perfil %s; se conserva el archivo original.',
                self.uuid,
            )


class PermissionProfile(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid_lib.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    permissions = models.ManyToManyField('auth.Permission', verbose_name='Permisos', blank=True)

    class Meta:
        verbose_name = 'Perfil de permisos'
        verbose_name_plural = 'Perfiles de permisos'
        ordering = ['name']
        default_permissions = ()
        permissions = [
            ('view_permissionprofile', 'Ver'),
            ('add_permissionprofile', 'Añadir'),
            ('change_permissionprofile', 'Editar'),
            ('delete_permissionprofile', 'Eliminar'),
        ]

    def __str__(self):
        return self.name


class GroupProfile(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid_lib.uuid4, editable=False)
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='profile')

    class Meta:
        verbose_name = 'Perfil de grupo'
        verbose_name_plural = 'Perfiles de grupos'
        default_permissions = ()
        permissions = [
            ('view_groupprofile', 'Ver perfiles de grupo'),
            ('add_groupprofile', 'Añadir perfiles de grupo'),
            ('change_groupprofile', 'Cambiar perfiles de grupo'),
            ('delete_groupprofile', 'Eliminar perfiles de grupo'),
        ]

    def __str__(self):
        return f'Perfil de {self.group.name}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=Group)
def create_group_profile(sender, instance, created, **kwargs):
    if created:
        GroupProfile.objects.get_or_create(group=instance)
