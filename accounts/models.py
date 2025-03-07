import os
import uuid

from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image

from common.utils import generic_image_path
from core import settings

# Create your models here.

class Profile(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE)
  avatar = models.ImageField(null=True, blank=True, upload_to=generic_image_path)
  uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

  def save(self, *args, **kwargs):
        try:
            this = Profile.objects.get(uuid=self.uuid)
            if this.avatar != self.avatar:
                this.avatar.delete(save=False)
        except:
            pass
        super(Profile, self).save(*args, **kwargs)

        if self.avatar and os.path.exists(self.avatar.path):
          # Redimencionar la imagen antes de guardarla
          with Image.open(self.avatar.path) as img:
              wide, hide = img.size
              if wide > hide:
                 # La imagen es mas ancha(wide) que alta(hide)
                 new_hide = 300
                 new_wide = int((wide/hide) * new_hide)
                 img = img.resize((new_wide, new_hide))
                 img.save(self.avatar.path)
              elif hide > wide:
                 # La imagen es mas alta(hide) que ancha(wide)
                 new_wide = 300
                 new_hide = int((hide/wide) * new_wide)
                 img = img.resize((new_wide, new_hide))
              else:
                 # La imagen es cuadrada
                 img.thumbnail((300, 300))
                 img.save(self.avatar.path)

            # Recorte de la imagen final
          with Image.open(self.avatar.path) as img:
            wide, hide = img.size
            if wide > hide:
               left = (wide - hide) / 2 
               top = 0  
               rigth = (wide + hide) / 2
               bottom = hide
            else:
               left = 0
               top = (hide -wide) / 2
               rigth = wide
               bottom = (hide + wide) /2 
            img = img.crop((left, top, rigth, bottom))
            img.save(self.avatar.path)  

  def delete(self, *args, **kwargs):
      self.avatar.delete(save=False)
      super(Profile, self).delete(*args, **kwargs)

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

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not instance._state.adding:
        instance.profile.save()

@receiver(post_save, sender=Group)
def create_group_profile(sender, instance, created, **kwargs):
    if created:
        GroupProfile.objects.create(group=instance)

@receiver(post_save, sender=Group)
def save_group_profile(sender, instance, **kwargs):
    if not instance._state.adding:
        instance.groupprofile.save()