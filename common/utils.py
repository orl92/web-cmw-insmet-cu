import os
import uuid

from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import default_storage
from django.db import models
from django.shortcuts import render
from django.templatetags.static import static
from django.views import View


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
    # Usamos el nombre de la clase del modelo concreto si existe
    class_name = instance.__class__.__name__.lower() if hasattr(instance, '__class__') else 'pdf'
    return 'pdf/{}/{}{}'.format(class_name, random_filename, extension)

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


class PDFModel(models.Model):
    """
    Modelo abstracto para manejar archivos PDF con eliminación automática.
    """
    file = models.FileField(upload_to=generic_pdf_path, verbose_name="Archivo PDF", blank=True, null=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para eliminar el archivo antiguo cuando se actualiza.
        """
        try:
            # Obtener instancia anterior de la base de datos
            this = self.__class__.objects.get(id=self.id)
            
            # Verificar si el archivo ha cambiado
            if this.file and this.file != self.file:
                # Eliminar el archivo antiguo del almacenamiento
                this.file.delete(save=False)
        except self.__class__.DoesNotExist:
            # Es una nueva instancia, no hay archivo antiguo que eliminar
            pass
        except Exception as e:
            # Capturar cualquier excepción para no interrumpir el guardado
            print(f"Error al eliminar archivo antiguo: {e}")
        
        super(PDFModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Sobrescribe el método delete para eliminar el archivo físico.
        """
        # Eliminar el archivo del almacenamiento
        if self.file:
            self.file.delete(save=False)
        
        super(PDFModel, self).delete(*args, **kwargs)

    def get_filename(self):
        """
        Obtener solo el nombre del archivo sin la ruta.
        """
        if self.file:
            return os.path.basename(self.file.name)
        return "Sin archivo"

    def get_file_url(self):
        """
        Obtener la URL completa del archivo.
        """
        if self.file:
            return f'{settings.MEDIA_URL}{self.file}'
        return None

    def get_file_path(self):
        """
        Obtener la ruta completa del archivo en el sistema de archivos.
        """
        if self.file:
            return self.file.path
        return None

    def file_exists(self):
        """
        Verificar si el archivo físico existe en el sistema de archivos.
        """
        if self.file:
            return default_storage.exists(self.file.name)
        return False

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