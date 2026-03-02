import os
import re
import uuid

from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.shortcuts import render
from django.templatetags.static import static
from django.views import View


def pdf_upload_path(instance, filename):
    """
    Genera la ruta para archivos PDF.
    Uso directo: upload_to=pdf_upload_path
    """
    ext = os.path.splitext(filename)[1]
    base = os.path.splitext(filename)[0]
    base = re.sub(r'[^a-zA-Z0-9_]', '_', base)
    random_name = str(uuid.uuid4())
    class_name = instance.__class__.__name__.lower()
    return f'pdf/{class_name}/{random_name}_{base}{ext}'


def image_upload_path(instance, filename, subfolder=None):
    """
    Genera la ruta para archivos de imagen.
    Uso directo: upload_to=image_upload_path
    """
    ext = os.path.splitext(filename)[1]
    base = os.path.splitext(filename)[0]
    base = re.sub(r'[^a-zA-Z0-9_]', '_', base)
    random_name = str(uuid.uuid4())
    class_name = instance.__class__.__name__.lower()

    return f'img/{class_name}/{random_name}_{base}{ext}'


class FileHandlerMixin(models.Model):
    """
    Mixin para eliminar archivos automáticamente al actualizar o eliminar.
    La clase hija debe definir `file_fields` como lista de nombres de campos FileField/ImageField.
    """
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        file_fields = getattr(self, 'file_fields', [])
        old_files = {}
        if self.pk and file_fields:
            try:
                old_instance = self.__class__.objects.get(pk=self.pk)
                for field in file_fields:
                    old_files[field] = getattr(old_instance, field, None)
            except self.__class__.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        for field in file_fields:
            old = old_files.get(field)
            new = getattr(self, field, None)
            if old and old != new:
                old.delete(save=False)

    def delete(self, *args, **kwargs):
        file_fields = getattr(self, 'file_fields', [])
        for field in file_fields:
            file = getattr(self, field, None)
            if file:
                file.delete(save=False)
        super().delete(*args, **kwargs)


# Mapa de códigos meteorológicos a nombres base de archivos
TIEMPO_IMG_BASE_MAP = {
    'PN': 'poco_nublado',
    'PARCN': 'parcialmente_nublado',
    'N': 'nublado',
    'AIS CHUB': 'aislados_chubascos',
    'ALG CHUB': 'algunos_chubascos',
    'NUM CHUB': 'numerosos_chubascos',
    'ALG TORM': 'algunas_tormentas',
    'NUM TORM': 'numerosas_tormentas',
}


# Códigos que usan la MISMA imagen para todos los períodos
CODIGOS_SIN_VARIACION = ['N', 'ALG TORM', 'NUM TORM', 'ALG CHUB', 'NUM CHUB']


# Sufijos para cada período
PERIOD_SUFFIXES = {
    'morning': 'm',
    'afternoon': 'a', 
    'night': 'n'
}


def get_img_path(weather_code, period='afternoon'):
    """
    Obtiene la ruta de la imagen según el código meteorológico y el período del día.
    Para códigos sin variación, usa siempre la imagen base.
    Para códigos con variación, usa el sufijo del período.
    """
    if weather_code not in TIEMPO_IMG_BASE_MAP:
        return ''  # O una imagen por defecto si prefieres
    
    base_name = TIEMPO_IMG_BASE_MAP[weather_code]
    
    # Si el código NO tiene variación entre períodos, usa solo el nombre base
    if weather_code in CODIGOS_SIN_VARIACION:
        file_path = f'dist/img/weather_icon/{base_name}.png'
    else:
        # Si el código SÍ tiene variación, usa el sufijo del período
        suffix = PERIOD_SUFFIXES.get(period, 'a')  # Por defecto 'a' (tarde)
        file_path = f'dist/img/weather_icon/{base_name}_{suffix}.png'
    
    return static(file_path)


# Funciones para la luna
def get_moon_img_path(moon_phase):
    MOON_IMG_MAP = {
        'Luna Nueva': 'dist/img/moon_faces/new_moon.png',
        'Creciente': 'dist/img/moon_faces/waning_crescent_moon.png',
        'Cuarto Creciente': 'dist/img/moon_faces/first_quarter_moon.png',
        'Gibosa Creciente': 'dist/img/moon_faces/waning_gibbous_moon.png',
        'Luna Llena': 'dist/img/moon_faces/full_moon.png',
        'Gibosa Menguante': 'dist/img/moon_faces/waxing_gibbous_moon.png',
        'Cuarto Menguante': 'dist/img/moon_faces/last_quarter_moon.png',
        'Menguante': 'dist/img/moon_faces/waxing_crescent_moon.png', 
    }
    file_path = MOON_IMG_MAP.get(moon_phase)
    return static(file_path) if file_path else ''


# Funciones para el sol
def get_sun_img_path(sun_event):
    SUN_IMG_MAP = {
        'sunrise': 'dist/img/sun/sunrise.png',
        'sunset': 'dist/img/sun/sunset.png',
    }
    file_path = SUN_IMG_MAP.get(sun_event)
    return static(file_path) if file_path else ''


def log_action(user, obj, action_flag, message=""):
    LogEntry.objects.log_action(
        user_id=user.pk,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=str(obj),
        action_flag=action_flag,
        change_message=message,
    )


class My400View(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'layouts/400.html', status=400)


class My403View(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'layouts/403.html', status=403)


class My404View(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'layouts/404.html', status=404)


class My500View(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'layouts/500.html', status=500)
