import os
import uuid

from django.conf import settings
from django.db import models

from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType

def generic_image_path(instance, filename):
    # Generar nombre aleatorio usando libreria uuid
    random_filename = str(uuid.uuid4())
    # Recuperar la extensión del archivo de imagen
    extension = os.path.splitext(filename)[1]
    # Devolver la ruta completa final del archivo
    return 'img/{}/{}{}'.format(instance.__class__.__name__.lower(), random_filename, extension)

def generic_pdf_path(instance, filename):
    # Generar nombre aleatorio usando la librería uuid
    random_filename = str(uuid.uuid4())
    # Recuperar la extensión del archivo PDF
    extension = os.path.splitext(filename)[1]
    # Devolver la ruta completa final del archivo
    return 'pdf/{}/{}{}'.format(instance.__class__.__name__.lower(), random_filename, extension)

class ImageModel(models.Model):
    image = models.ImageField(upload_to=generic_image_path, verbose_name='Imágen')

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        try:
            this = self.__class__.objects.get(id=self.id)
            if this.image != self.image:
                this.image.delete(save=False)
        except self.__class__.DoesNotExist:
            pass
        super(ImageModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.image.delete(save=False)
        super(ImageModel, self).delete(*args, **kwargs)

    def get_image(self):
        if self.image:
            return f'{settings.MEDIA_URL}{self.image}'
        return f'{settings.STATIC_URL}dist/img/default.svg'
    
TIEMPO_IMG_MAP = {
    'PN': 'static/dist/img/weather_icon/poco_nublado.png',
    'PARCN': 'static/dist/img/weather_icon/parcialmente_nublado.png',
    'N': 'static/dist/img/weather_icon/nublado.png',
    'AIS CHUB': 'static/dist/img/weather_icon/aislados_chubascos.png',
    'ALG CHUB': 'static/dist/img/weather_icon/algunos_chubascos.png',
    'NUM CHUB': 'static/dist/img/weather_icon/numerosos_chubascos.png',
    'ALG TORM': 'static/dist/img/weather_icon/algunas_tormentas.png',
    'NUM TORM': 'static/dist/img/weather_icon/numerosas_tormentas.png',
    'PN_NIGHT': 'static/dist/img/weather_icon/poco_nublado_noche.png',
    'PARCN_NIGHT': 'static/dist/img/weather_icon/parcialmente_nublado_noche.png',
    'N_NIGHT': 'static/dist/img/weather_icon/nublado_noche.png',
    'AIS CHUB_NIGHT': 'static/dist/img/weather_icon/aislados_chubascos_noche.png',
    'ALG CHUB_NIGHT': 'static/dist/img/weather_icon/algunos_chubascos_noche.png',
    'NUM CHUB_NIGHT': 'static/dist/img/weather_icon/numerosos_chubascos_noche.png',
    'ALG TORM_NIGHT': 'static/dist/img/weather_icon/algunas_tormentas_noche.png',
    'NUM TORM_NIGHT': 'static/dist/img/weather_icon/numerosas_tormentas_noche.png',
}

def get_img_path(weather_code, is_night=False):
    if is_night:
        return TIEMPO_IMG_MAP.get(f"{weather_code}_NIGHT")
    return TIEMPO_IMG_MAP.get(weather_code)

MOON_IMG_MAP = {
    'Luna Nueva': 'static/dist/img/moon_faces/new_moon.png',
    'Creciente': 'static/dist/img/moon_faces/waning_crescent_moon.png',
    'Cuarto Creciente': 'static/dist/img/moon_faces/first_quarter_moon.png',
    'Gibosa Creciente': 'static/dist/img/moon_faces/waning_gibbous_moon.png',
    'Luna Llena': 'static/dist/img/moon_faces/full_moon.png',
    'Gibosa Menguante': 'static/dist/img/moon_faces/waxing_gibbous_moon.png',
    'Cuarto Menguante': 'static/dist/img/moon_faces/last_quarter_moon.png',
    'Menguante': 'static/dist/img/moon_faces/waxing_crescent_moon.png', 
}

def get_moon_img_path(moon_code):
    return MOON_IMG_MAP.get(moon_code)

SUN_IMG_MAP = {
    'sunrise': 'static/dist/img/sun/sunrise.png',
    'sunset': 'static/dist/img/sun/sunset.png',
}

def get_sun_img_path(sun_code):
    return SUN_IMG_MAP.get(sun_code)

def log_action(user, obj, action_flag, message=""):
    LogEntry.objects.log_action(
        user_id=user.pk,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=str(obj),
        action_flag=action_flag,
        change_message=message,
    )
