import os
import re

from django import template
from django.utils.timesince import timesince
from django.utils.translation import gettext as _
from django.templatetags.static import static

register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    return value.as_widget(attrs={'class': arg})

@register.filter(name='add_attrs')
def add_attrs(field, attrs):
    attrs = attrs.split(',')
    attrs_dict = {attr.split(':')[0].strip(): attr.split(':')[1].strip() for attr in attrs}
    return field.as_widget(attrs=attrs_dict)

@register.filter
def filename(value):
    return os.path.splitext(os.path.basename(value))[0]

@register.filter 
def has_permission(user, perm): 
    return user.has_perm(perm)

@register.filter(name='remove_images_and_special_chars')
def remove_images_and_special_chars(value):
    # Eliminar etiquetas de imagen
    value = re.sub(r'<img[^>]*>', '', value)
    # Eliminar caracteres especiales no deseados
    value = re.sub(r'&nbsp;', ' ', value)
    return value

@register.filter
def action_description(action_flag):
    descriptions = {
        1: "Adición",
        2: "Cambio",
        3: "Eliminación",
        4: "Inicio de Sesión",
        5: "Cierre de Sesión"
    }
    return descriptions.get(action_flag, "Acción Desconocida")

@register.filter
def get_icon_for_action(action_flag):
    icons = {
        1: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="green" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-circle-plus"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0" /><path d="M9 12h6" /><path d="M12 9v6" /></svg>',  # Icono para agregar (verde)
        2: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="orange" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-edit"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7h-1a2 2 0 0 0 -2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2 -2v-1" /><path d="M20.385 6.585a2.1 2.1 0 0 0 -2.97 -2.97l-8.415 8.385v3h3l8.385 -8.415z" /><path d="M16 5l3 3" /></svg>',  # Icono para cambiar (naranja)
        3: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="red" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-trash"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M4 7l16 0" /><path d="M10 11l0 6" /><path d="M14 11l0 6" /><path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12" /><path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3" /></svg>',  # Icono para eliminar (rojo)
        4: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="green" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icon-tabler-login-2"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M9 8v-2a2 2 0 0 1 2 -2h7a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-7a2 2 0 0 1 -2 -2v-2" /><path d="M3 12h13l-3 -3" /><path d="M13 15l3 -3" /></svg>',  # Icono para inicio de sesión (verde)
        5: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="red" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-logout"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M14 8v-2a2 2 0 0 0 -2 -2h-7a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h7a2 2 0 0 0 2 -2v-2" /><path d="M9 12h12l-3 -3" /><path d="M18 15l3 -3" /></svg>'  # Icono para cierre de sesión (rojo)
    }
    return icons.get(action_flag, '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="gray" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-info-circle"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0" /><path d="M12 9h.01" /><path d="M11 12h1v4h1" /></svg>')  # Icono por defecto (gris)

@register.filter
def time_since(value):
    return _('hace %(timesince)s') % {'timesince': timesince(value)}

@register.filter
def get_tiempo_description(value):
    TIEMPO_DESCRIPCIONES = {
        'PN': 'Poco Nublado',
        'PARCN': 'Parcialmente Nublado',
        'N': 'Nublado',
        'AIS CHUB': 'Aislados Chubascos',
        'ALG CHUB': 'Algunos Chubascos',
        'NUM CHUB': 'Numerosos Chubascos',
        'ALG TORM': 'Algunas Tormentas',
        'NUM TORM': 'Numerosas Tormentas',
    }
    return TIEMPO_DESCRIPCIONES.get(value, 'Descripción no disponible')

MAR_DESCRIPCIONES = {
    'TQ': 'Tranquila',
    'PO': 'Poco Oleaje',
    'O': 'Oleaje',
    'MRJ': 'Marejadas',
    'FMRJ': 'Fuertes Marejadas',
}

@register.filter
def get_mar_description(value):
    return MAR_DESCRIPCIONES.get(value, 'Descripción no disponible')

# Mapa de imágenes del tiempo
TIEMPO_IMG_MAP = {
    'PN': 'dist/img/weather_icon/poco_nublado.png',
    'PARCN': 'dist/img/weather_icon/parcialmente_nublado.png',
    'N': 'dist/img/weather_icon/nublado.png',
    'AIS CHUB': 'dist/img/weather_icon/aislados_chubascos.png',
    'ALG CHUB': 'dist/img/weather_icon/algunos_chubascos.png',
    'NUM CHUB': 'dist/img/weather_icon/numerosos_chubascos.png',
    'ALG TORM': 'dist/img/weather_icon/algunas_tormentas.png',
    'NUM TORM': 'dist/img/weather_icon/numerosas_tormentas.png',
    'PN_NIGHT': 'dist/img/weather_icon/poco_nublado_noche.png',
    'PARCN_NIGHT': 'dist/img/weather_icon/parcialmente_nublado_noche.png',
    'N_NIGHT': 'dist/img/weather_icon/nublado_noche.png',
    'AIS CHUB_NIGHT': 'dist/img/weather_icon/aislados_chubascos_noche.png',
    'ALG CHUB_NIGHT': 'dist/img/weather_icon/algunos_chubascos_noche.png',
    'NUM CHUB_NIGHT': 'dist/img/weather_icon/numerosos_chubascos_noche.png',
    'ALG TORM_NIGHT': 'dist/img/weather_icon/algunas_tormentas_noche.png',
    'NUM TORM_NIGHT': 'dist/img/weather_icon/numerosas_tormentas_noche.png',
}

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

SUN_IMG_MAP = {
    'sunrise': 'dist/img/sun/sunrise.png',
    'sunset': 'dist/img/sun/sunset.png',
}

@register.filter
def get_weather_img(weather_code, is_night=False):
    """Retorna la ruta de la imagen de tiempo según el código."""
    file_key = f"{weather_code}_NIGHT" if is_night else weather_code
    file_path = TIEMPO_IMG_MAP.get(file_key, '')
    return static(file_path) if file_path else ''

@register.filter
def get_moon_img(moon_phase):
    """Retorna la ruta de la imagen de la fase lunar."""
    return static(MOON_IMG_MAP.get(moon_phase, ''))

@register.filter
def get_sun_img(sun_event):
    """Retorna la ruta de la imagen de salida o puesta del sol."""
    return static(SUN_IMG_MAP.get(sun_event, ''))







