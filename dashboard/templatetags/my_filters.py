import os
import re

from django import template
from django.templatetags.static import static
from django.utils.timesince import timesince
from django.utils.translation import gettext as _

from common.utils import get_img_path  # Importa la función unificada

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
        5: "Cierre de Sesión",
        6: "Modo de Mantenimiento (activado/desactivado)"
    }
    return descriptions.get(action_flag, "Acción Desconocida")

@register.filter
def get_icon_for_action(action_flag):
    icons = {
        1: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="green" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-circle-plus"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0" /><path d="M9 12h6" /><path d="M12 9v6" /></svg>',
        2: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="orange" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-edit"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7h-1a2 2 0 0 0 -2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2 -2v-1" /><path d="M20.385 6.585a2.1 2.1 0 0 0 -2.97 -2.97l-8.415 8.385v3h3l8.385 -8.415z" /><path d="M16 5l3 3" /></svg>',
        3: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="red" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-trash"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M4 7l16 0" /><path d="M10 11l0 6" /><path d="M14 11l0 6" /><path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12" /><path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3" /></svg>',
        4: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="green" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icon-tabler-login-2"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M9 8v-2a2 2 0 0 1 2 -2h7a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-7a2 2 0 0 1 -2 -2v-2" /><path d="M3 12h13l-3 -3" /><path d="M13 15l3 -3" /></svg>',
        5: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="red" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-logout"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M14 8v-2a2 2 0 0 0 -2 -2h-7a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h7a2 2 0 0 0 2 -2v-2" /><path d="M9 12h12l-3 -3" /><path d="M18 15l3 -3" /></svg>',
        6: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-settings"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M10.325 4.317c.426 -1.756 2.924 -1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543 -.94 3.31 .826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756 .426 1.756 2.924 0 3.35a1.724 1.724 0 0 0 -1.066 2.573c.94 1.543 -.826 3.31 -2.37 2.37a1.724 1.724 0 0 0 -2.572 1.065c-.426 1.756 -2.924 1.756 -3.35 0a1.724 1.724 0 0 0 -2.573 -1.066c-1.543 .94 -3.31 -.826 -2.37 -2.37a1.724 1.724 0 0 0 -1.065 -2.572c-1.756 -.426 -1.756 -2.924 0 -3.35a1.724 1.724 0 0 0 1.066 -2.573c-.94 -1.543 .826 -3.31 2.37 -2.37c1 .608 2.296 .07 2.572 -1.065z" /><path d="M9 12a3 3 0 1 0 6 0a3 3 0 0 0 -6 0" /></svg>'
    }
    return icons.get(action_flag, '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="gray" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-info-circle"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0" /><path d="M12 9h.01" /><path d="M11 12h1v4h1" /></svg>')

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

LUNA_DESCRIPCIONES = {
    'Luna Nueva': 'La luna no es visible desde la Tierra',
    'Creciente': 'Fase creciente de la luna',
    'Cuarto Creciente': 'Mitad derecha iluminada',
    'Gibosa Creciente': 'Más de la mitad iluminada',
    'Luna Llena': 'Disco lunar completamente visible',
    'Gibosa Menguante': 'Más de la mitad oscurecida',
    'Cuarto Menguante': 'Mitad izquierda iluminada',
    'Menguante': 'Fase menguante final'
}

@register.filter
def get_luna_description(value):
    return LUNA_DESCRIPCIONES.get(value, 'Descripción no disponible')

SOL_DESCRIPCIONES = {
    'sunrise': 'Hora oficial de salida del sol',
    'sunset': 'Hora oficial de puesta del sol'
}

@register.filter
def get_sol_description(value):
    return SOL_DESCRIPCIONES.get(value, 'Descripción no disponible')

# Filtros para las imágenes del tiempo
@register.filter
def get_weather_img_morning(weather_code):
    """Para la mañana"""
    return get_img_path(weather_code, 'morning')

@register.filter
def get_weather_img_afternoon(weather_code):
    """Para la tarde"""
    return get_img_path(weather_code, 'afternoon')

@register.filter
def get_weather_img_night(weather_code):
    """Para la noche"""
    return get_img_path(weather_code, 'night')

# Filtro genérico
@register.filter
def get_weather_img(weather_code, period='afternoon'):
    """Filtro genérico que acepta el período como parámetro"""
    return get_img_path(weather_code, period)

# Filtros para la luna y el sol
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

@register.filter
def get_moon_img(moon_phase):
    """Retorna la ruta de la imagen de la fase lunar."""
    return static(MOON_IMG_MAP.get(moon_phase, ''))

SUN_IMG_MAP = {
    'sunrise': 'dist/img/sun/sunrise.png',
    'sunset': 'dist/img/sun/sunset.png',
}

@register.filter
def get_sun_img(sun_event):
    """Retorna la ruta de la imagen de salida o puesta del sol."""
    return static(SUN_IMG_MAP.get(sun_event, ''))

@register.filter
def get_forecast_day(obj, day_number):
    """Obtiene los datos de un día específico del pronóstico"""
    day_number = str(day_number)  # Asegurar conversión a string
    return {
        'date': getattr(obj, f'day{day_number}_date', '--'),
        'weather': getattr(obj, f'day{day_number}_weather', '--'),
        'max_temp': getattr(obj, f'day{day_number}_max_temp', '--'),
        'min_temp': getattr(obj, f'day{day_number}_min_temp', '--'),
    }

@register.filter
def get_dict_value(dictionary, key):
    """Obtiene un valor de un diccionario"""
    return dictionary.get(key, '--')

@register.filter
def get_permission_type(perm_name):
    """Determina el tipo de permiso basado en palabras clave"""
    perm_name_lower = perm_name.lower()
    if any(keyword in perm_name_lower for keyword in ['view', 'ver']):
        return 'view'
    elif any(keyword in perm_name_lower for keyword in ['add', 'añadir', 'crear']):
        return 'add'
    elif any(keyword in perm_name_lower for keyword in ['change', 'edit', 'editar', 'modificar']):
        return 'change'
    elif any(keyword in perm_name_lower for keyword in ['delete', 'eliminar', 'borrar']):
        return 'delete'
    else:
        return 'other'

@register.filter
def sort_permissions_by_type(permissions):
    """Ordena permisos por tipo: view, add, change, delete, other"""
    from collections import defaultdict
    
    # Agrupar por tipo
    grouped = defaultdict(list)
    for perm in permissions:
        perm_type = get_permission_type(perm.name)
        grouped[perm_type].append(perm)
    
    # Ordenar según el orden deseado
    ordered_types = ['view', 'add', 'change', 'delete', 'other']
    result = []
    
    for perm_type in ordered_types:
        if perm_type in grouped:
            # Ordenar alfabéticamente dentro de cada tipo
            sorted_perms = sorted(grouped[perm_type], key=lambda x: x.name.lower())
            result.extend(sorted_perms)
    
    return result

@register.filter
def group_permissions_by_app(permissions):
    """Agrupa permisos por aplicación y modelo"""
    from collections import defaultdict
    
    grouped = defaultdict(lambda: defaultdict(list))
    
    for perm in permissions:
        # Extraer app_label y model del codename (formato: app_label.model)
        # Django permissions tienen formato: <action>_<modelname>
        # Pero también podemos usar el content_type si está disponible
        app_label = perm.content_type.app_label if hasattr(perm, 'content_type') else 'unknown'
        model_name = perm.content_type.model if hasattr(perm, 'content_type') else 'unknown'
        
        # Determinar tipo de permiso
        perm_type = get_permission_type(perm.name)
        
        grouped[app_label][model_name].append({
            'perm': perm,
            'type': perm_type
        })
    
    # Convertir a estructura ordenada
    result = []
    for app_label in sorted(grouped.keys()):
        models = []
        for model_name in sorted(grouped[app_label].keys()):
            models.append({
                'name': model_name,
                'permissions': grouped[app_label][model_name]
            })
        result.append({
            'app_label': app_label,
            'models': models
        })
    
    return result

@register.filter
def filter_permissions_by_type(permissions, perm_type):
    """Filtra permisos por tipo"""
    return [p for p in permissions if get_permission_type(p.name) == perm_type]

@register.filter
def exclude_permissions_by_type(permissions, types_to_exclude):
    """Excluye permisos por tipo(s)"""
    types_list = [t.strip() for t in types_to_exclude.split(',')]
    return [p for p in permissions if get_permission_type(p.name) not in types_list]
