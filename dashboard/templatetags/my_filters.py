import os
import re
from collections import defaultdict

from django import template
from django.templatetags.static import static
from django.utils.timesince import timesince
from django.utils.translation import gettext as _

from common.utils import get_img_path

register = template.Library()

# ============================================================================
# FILTROS PARA FORMULARIOS Y CAMPOS
# ============================================================================


@register.filter(name="add_class")
def add_class(value, arg):
    """
    Agrega una clase CSS a un widget de formulario.

    Args:
        value: Campo del formulario
        arg (str): Nombre de la clase CSS a agregar

    Returns:
        Widget del campo con la clase añadida

    Uso en plantilla: {{ field|add_class:"form-control" }}
    """
    return value.as_widget(attrs={"class": arg})


@register.filter(name="add_attrs")
def add_attrs(field, attrs):
    """
    Agrega múltiples atributos a un widget de formulario.

    Args:
        field: Campo del formulario
        attrs (str): Cadena con atributos separados por comas en formato "atributo:valor"

    Returns:
        Widget del campo con los atributos añadidos

    Uso en plantilla: {{ field|add_attrs:"placeholder:Ingrese texto,data-toggle:modal" }}
    """
    attrs = attrs.split(",")
    attrs_dict = {
        attr.split(":")[0].strip(): attr.split(":")[1].strip() for attr in attrs
    }
    return field.as_widget(attrs=attrs_dict)


@register.filter
def filename(value):
    """
    Extrae el nombre base de un archivo sin la extensión.

    Args:
        value (str): Ruta completa del archivo

    Returns:
        str: Nombre del archivo sin extensión

    Uso en plantilla: {{ file_path|filename }}
    """
    return os.path.splitext(os.path.basename(value))[0]


# ============================================================================
# FILTROS PARA PERMISOS Y AUTENTICACIÓN
# ============================================================================


@register.filter
def has_permission(user, perm):
    """
    Verifica si un usuario tiene un permiso específico.

    Args:
        user: Objeto usuario de Django
        perm (str): Código del permiso (ej: 'app.codename')

    Returns:
        bool: True si el usuario tiene el permiso, False en caso contrario

    Uso en plantilla: {% if user|has_permission:"app.view_model" %}
    """
    return user.has_perm(perm)


@register.filter
def in_group_permissions(permission, group_permissions):
    """
    Verifica si un permiso está en la lista de permisos de un grupo.

    Args:
        permission: Objeto Permission
        group_permissions: QuerySet o lista de permisos del grupo

    Returns:
        bool: True si el permiso está en el grupo, False en caso contrario

    Uso en plantilla: {% if perm|in_group_permissions:group.permissions.all %}
    """
    return permission in group_permissions


# ============================================================================
# FILTROS PARA MANIPULACIÓN DE TEXTO Y HTML
# ============================================================================


@register.filter(name="remove_images_and_special_chars")
def remove_images_and_special_chars(value):
    """
    Elimina etiquetas <img> y caracteres especiales &nbsp; de un texto HTML.

    Args:
        value (str): Texto HTML a limpiar

    Returns:
        str: Texto limpio sin imágenes ni &nbsp;

    Uso en plantilla: {{ html_content|remove_images_and_special_chars }}
    """
    value = re.sub(r"<img[^>]*>", "", value)
    value = re.sub(r"&nbsp;", " ", value)
    return value


@register.filter
def get_dict_value(dictionary, key):
    """
    Obtiene un valor de un diccionario con valor por defecto.

    Args:
        dictionary (dict): Diccionario de donde obtener el valor
        key: Clave a buscar en el diccionario

    Returns:
        Valor correspondiente a la clave o "--" si no existe

    Uso en plantilla: {{ my_dict|get_dict_value:"key_name" }}
    """
    return dictionary.get(key, "--")


# ============================================================================
# FILTROS PARA REGISTROS DE ACTIVIDAD (LOGS)
# ============================================================================


@register.filter
def action_description(action_flag):
    """
    Convierte un código de acción en su descripción en español.

    Args:
        action_flag (int): Código numérico de la acción (1-6)

    Returns:
        str: Descripción legible de la acción

    Mapeo de códigos:
        1: Adición, 2: Cambio, 3: Eliminación
        4: Inicio de Sesión, 5: Cierre de Sesión
        6: Modo de Mantenimiento (activado/desactivado)

    Uso en plantilla: {{ log.action_flag|action_description }}
    """
    descriptions = {
        1: "Adición",
        2: "Cambio",
        3: "Eliminación",
        4: "Inicio de Sesión",
        5: "Cierre de Sesión",
        6: "Modo de Mantenimiento (activado/desactivado)",
    }
    return descriptions.get(action_flag, "Acción Desconocida")


@register.filter
def get_icon_for_action(action_flag):
    """
    Devuelve un ícono SVG correspondiente al tipo de acción.

    Args:
        action_flag (int): Código numérico de la acción

    Returns:
        str: Código HTML del ícono SVG con colores apropiados

    Uso en plantilla: {{ log.action_flag|get_icon_for_action|safe }}
    """
    icons = {
        1: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="green" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-circle-plus"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0" /><path d="M9 12h6" /><path d="M12 9v6" /></svg>',
        2: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="orange" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-edit"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7h-1a2 2 0 0 0 -2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2 -2v-1" /><path d="M20.385 6.585a2.1 2.1 0 0 0 -2.97 -2.97l-8.415 8.385v3h3l8.385 -8.415z" /><path d="M16 5l3 3" /></svg>',
        3: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="red" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-trash"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M4 7l16 0" /><path d="M10 11l0 6" /><path d="M14 11l0 6" /><path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12" /><path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3" /></svg>',
        4: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="green" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icon-tabler-login-2"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M9 8v-2a2 2 0 0 1 2 -2h7a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-7a2 2 0 0 1 -2 -2v-2" /><path d="M3 12h13l-3 -3" /><path d="M13 15l3 -3" /></svg>',
        5: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="red" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-logout"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M14 8v-2a2 2 0 0 0 -2 -2h-7a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h7a2 2 0 0 0 2 -2v-2" /><path d="M9 12h12l-3 -3" /><path d="M18 15l3 -3" /></svg>',
        6: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-settings"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M10.325 4.317c.426 -1.756 2.924 -1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543 -.94 3.31 .826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756 .426 1.756 2.924 0 3.35a1.724 1.724 0 0 0 -1.066 2.573c.94 1.543 -.826 3.31 -2.37 2.37a1.724 1.724 0 0 0 -2.572 1.065c-.426 1.756 -2.924 1.756 -3.35 0a1.724 1.724 0 0 0 -2.573 -1.066c-1.543 .94 -3.31 -.826 -2.37 -2.37a1.724 1.724 0 0 0 -1.065 -2.572c-1.756 -.426 -1.756 -2.924 0 -3.35a1.724 1.724 0 0 0 1.066 -2.573c-.94 -1.543 .826 -3.31 2.37 -2.37c1 .608 2.296 .07 2.572 -1.065z" /><path d="M9 12a3 3 0 1 0 6 0a3 3 0 0 0 -6 0" /></svg>',
    }
    return icons.get(
        action_flag,
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="gray" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-info-circle"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0" /><path d="M12 9h.01" /><path d="M11 12h1v4h1" /></svg>',
    )


@register.filter
def time_since(value):
    """
    Formatea una fecha en un formato relativo "hace X tiempo".

    Args:
        value (datetime): Fecha a formatear

    Returns:
        str: Texto formateado (ej: "hace 2 horas")

    Uso en plantilla: {{ user.last_login|time_since }}
    """
    return _("hace %(timesince)s") % {"timesince": timesince(value)}


# ============================================================================
# FILTROS METEOROLÓGICOS - DESCRIPCIONES
# ============================================================================


@register.filter
def get_tiempo_description(value):
    """
    Obtiene la descripción completa de un código meteorológico.

    Args:
        value (str): Código meteorológico (ej: "PN", "N", "ALG CHUB")

    Returns:
        str: Descripción completa en español

    Uso en plantilla: {{ forecast.nwm|get_tiempo_description }}
    """
    TIEMPO_DESCRIPCIONES = {
        "PN": "Poco Nublado",
        "PARCN": "Parcialmente Nublado",
        "N": "Nublado",
        "AIS CHUB": "Aislados Chubascos",
        "ALG CHUB": "Algunos Chubascos",
        "NUM CHUB": "Numerosos Chubascos",
        "ALG TORM": "Algunas Tormentas",
        "NUM TORM": "Numerosas Tormentas",
    }
    return TIEMPO_DESCRIPCIONES.get(value, "Descripción no disponible")


@register.filter
def get_mar_description(value):
    """
    Obtiene la descripción completa del estado del mar.

    Args:
        value (str): Código del estado del mar (ej: "TQ", "O", "MRJ")

    Returns:
        str: Descripción completa en español

    Uso en plantilla: {{ forecast.nsm|get_mar_description }}
    """
    MAR_DESCRIPCIONES = {
        "TQ": "Tranquila",
        "PO": "Poco Oleaje",
        "O": "Oleaje",
        "MRJ": "Marejadas",
        "FMRJ": "Fuertes Marejadas",
    }
    return MAR_DESCRIPCIONES.get(value, "Descripción no disponible")


@register.filter
def get_luna_description(value):
    """
    Obtiene la descripción de una fase lunar.

    Args:
        value (str): Nombre de la fase lunar

    Returns:
        str: Descripción científica de la fase lunar

    Uso en plantilla: {{ moon_phase|get_luna_description }}
    """
    LUNA_DESCRIPCIONES = {
        "Luna Nueva": "La luna no es visible desde la Tierra",
        "Creciente": "Fase creciente de la luna",
        "Cuarto Creciente": "Mitad derecha iluminada",
        "Gibosa Creciente": "Más de la mitad iluminada",
        "Luna Llena": "Disco lunar completamente visible",
        "Gibosa Menguante": "Más de la mitad oscurecida",
        "Cuarto Menguante": "Mitad izquierda iluminada",
        "Menguante": "Fase menguante final",
    }
    return LUNA_DESCRIPCIONES.get(value, "Descripción no disponible")


@register.filter
def get_sol_description(value):
    """
    Obtiene la descripción de un evento solar.

    Args:
        value (str): Tipo de evento solar ("sunrise" o "sunset")

    Returns:
        str: Descripción del evento solar

    Uso en plantilla: {{ sun_event|get_sol_description }}
    """
    SOL_DESCRIPCIONES = {
        "sunrise": "Hora oficial de salida del sol",
        "sunset": "Hora oficial de puesta del sol",
    }
    return SOL_DESCRIPCIONES.get(value, "Descripción no disponible")


# ============================================================================
# FILTROS METEOROLÓGICOS - IMÁGENES
# ============================================================================


@register.filter
def get_weather_img_morning(weather_code):
    """
    Obtiene la ruta de la imagen para el tiempo matutino.

    Args:
        weather_code (str): Código meteorológico

    Returns:
        str: Ruta de la imagen correspondiente

    Uso en plantilla: {{ forecast.nwm|get_weather_img_morning }}
    """
    return get_img_path(weather_code, "morning")


@register.filter
def get_weather_img_afternoon(weather_code):
    """
    Obtiene la ruta de la imagen para el tiempo vespertino.

    Args:
        weather_code (str): Código meteorológico

    Returns:
        str: Ruta de la imagen correspondiente

    Uso en plantilla: {{ forecast.nwa|get_weather_img_afternoon }}
    """
    return get_img_path(weather_code, "afternoon")


@register.filter
def get_weather_img_night(weather_code):
    """
    Obtiene la ruta de la imagen para el tiempo nocturno.

    Args:
        weather_code (str): Código meteorológico

    Returns:
        str: Ruta de la imagen correspondiente

    Uso en plantilla: {{ forecast.nwn|get_weather_img_night }}
    """
    return get_img_path(weather_code, "night")


@register.filter
def get_weather_img(weather_code, period="afternoon"):
    """
    Obtiene la ruta de la imagen para un período específico del día.

    Args:
        weather_code (str): Código meteorológico
        period (str): Período del día ("morning", "afternoon", "night")

    Returns:
        str: Ruta de la imagen correspondiente

    Uso en plantilla: {{ forecast.nwm|get_weather_img:"morning" }}
    """
    return get_img_path(weather_code, period)


@register.filter
def get_moon_img(moon_phase):
    """
    Obtiene la ruta de la imagen para una fase lunar.

    Args:
        moon_phase (str): Nombre de la fase lunar

    Returns:
        str: URL estática de la imagen lunar

    Uso en plantilla: {{ moon_phase|get_moon_img }}
    """
    MOON_IMG_MAP = {
        "Luna Nueva": "dist/img/moon_faces/new_moon.png",
        "Creciente": "dist/img/moon_faces/waning_crescent_moon.png",
        "Cuarto Creciente": "dist/img/moon_faces/first_quarter_moon.png",
        "Gibosa Creciente": "dist/img/moon_faces/waning_gibbous_moon.png",
        "Luna Llena": "dist/img/moon_faces/full_moon.png",
        "Gibosa Menguante": "dist/img/moon_faces/waxing_gibbous_moon.png",
        "Cuarto Menguante": "dist/img/moon_faces/last_quarter_moon.png",
        "Menguante": "dist/img/moon_faces/waxing_crescent_moon.png",
    }
    return static(MOON_IMG_MAP.get(moon_phase, ""))


@register.filter
def get_sun_img(sun_event):
    """
    Obtiene la ruta de la imagen para un evento solar.

    Args:
        sun_event (str): Tipo de evento ("sunrise" o "sunset")

    Returns:
        str: URL estática de la imagen solar

    Uso en plantilla: {{ sun_event|get_sun_img }}
    """
    SUN_IMG_MAP = {
        "sunrise": "dist/img/sun/sunrise.png",
        "sunset": "dist/img/sun/sunset.png",
    }
    return static(SUN_IMG_MAP.get(sun_event, ""))


@register.filter
def get_forecast_day(obj, day_number):
    """
    Extrae los datos de pronóstico para un día específico.

    Args:
        obj: Objeto de pronóstico con campos dayX_*
        day_number (int): Número del día (1-5)

    Returns:
        dict: Diccionario con fecha, tiempo, temp max y min para el día

    Uso en plantilla: {{ forecast|get_forecast_day:1 }}
    """
    day_number = str(day_number)
    return {
        "date": getattr(obj, f"day{day_number}_date", "--"),
        "weather": getattr(obj, f"day{day_number}_weather", "--"),
        "max_temp": getattr(obj, f"day{day_number}_max_temp", "--"),
        "min_temp": getattr(obj, f"day{day_number}_min_temp", "--"),
    }


# ============================================================================
# FILTROS PARA GESTIÓN DE PERMISOS Y GRUPOS
# ============================================================================


@register.filter
def get_model_verbose_name(permission):
    """
    Obtiene el verbose_name del modelo asociado a un permiso.

    Args:
        permission: Objeto Permission de Django

    Returns:
        str: Nombre legible del modelo en español

    Uso en plantilla: {{ permission|get_model_verbose_name }}
    """
    try:
        model_class = permission.content_type.model_class()
        if model_class:
            return model_class._meta.verbose_name
    except:
        pass

    return permission.content_type.model.replace("_", " ").title()


@register.filter
def get_permission_type_from_codename(permission):
    """
    Determina el tipo de permiso basado en su código.

    Args:
        permission: Objeto Permission de Django

    Returns:
        str: Tipo de permiso ("view", "add", "change", "delete", "other")

    Uso en plantilla: {{ permission|get_permission_type_from_codename }}
    """
    codename = permission.codename.lower()
    if codename.startswith("view_"):
        return "view"
    elif codename.startswith("add_"):
        return "add"
    elif codename.startswith("change_"):
        return "change"
    elif codename.startswith("delete_"):
        return "delete"
    else:
        return "other"


@register.filter
def filter_permissions_by_type(permissions, perm_type):
    """
    Filtra una lista de permisos por tipo específico.

    Args:
        permissions: Lista o QuerySet de permisos
        perm_type (str): Tipo de permiso a filtrar

    Returns:
        list: Lista de permisos del tipo especificado

    Uso en plantilla: {{ group.permissions.all|filter_permissions_by_type:"view" }}
    """
    return [p for p in permissions if get_permission_type_from_codename(p) == perm_type]


@register.filter
def group_permissions_for_table(permissions):
    """
    Agrupa permisos para mostrar en tablas de edición de grupos.

    Args:
        permissions: Lista o QuerySet de permisos

    Returns:
        dict: Diccionario estructurado por modelo y tipo de permiso
              Formato: {model_name: {"view": perm_obj, "add": perm_obj, ...}}

    Uso en plantilla: {{ permissions|group_permissions_for_table }}
    """
    grouped = defaultdict(
        lambda: {"view": None, "add": None, "change": None, "delete": None}
    )

    for perm in permissions:
        # Obtener el nombre del modelo (verbose_name)
        model_name = get_model_verbose_name(perm)

        # Determinar tipo de permiso
        perm_type = get_permission_type_from_codename(perm)

        if perm_type in ["view", "add", "change", "delete"]:
            grouped[model_name][perm_type] = {
                "perm": perm,
                "field_name": "permissions",
                "field_id": f"perm_{perm.id}",
                "is_checked": False,
            }

    # Ordenar por nombre del modelo
    return dict(sorted(grouped.items()))


@register.filter
def group_permissions_for_modal(permissions):
    """
    Agrupa permisos para mostrar en modales del dashboard.

    Args:
        permissions: Lista o QuerySet de permisos

    Returns:
        list: Lista estructurada por aplicación y modelo
              Formato: [{"app_label": "app", "models": [{"name": "Model", "permissions": {...}}]}]

    Uso en plantilla: {{ group.permissions.all|group_permissions_for_modal }}
    """
    grouped = defaultdict(
        lambda: defaultdict(
            lambda: {"view": False, "add": False, "change": False, "delete": False}
        )
    )

    for perm in permissions:
        app_label = perm.content_type.app_label

        # Obtener el verbose_name del modelo
        model_display_name = get_model_verbose_name(perm)

        # Determinar tipo de permiso
        perm_type = get_permission_type_from_codename(perm)

        if perm_type in ["view", "add", "change", "delete"]:
            grouped[app_label][model_display_name][perm_type] = True

    # Convertir a la estructura para el modal
    result = []
    for app_label in sorted(grouped.keys()):
        models = []
        for model_display_name, perms in grouped[app_label].items():
            models.append({"name": model_display_name, "permissions": perms})

        result.append(
            {"app_label": app_label, "models": sorted(models, key=lambda x: x["name"])}
        )

    return result


# ============================================================================
# FILTROS PARA COLORES Y ESTILOS DE PERMISOS
# ============================================================================


@register.filter
def get_permission_badge_class(perm_type):
    """
    Devuelve la clase CSS para badges según el tipo de permiso.

    Args:
        perm_type (str): Tipo de permiso ("view", "add", "change", "delete", "other")

    Returns:
        str: Clase CSS para el badge (ej: "bg-green-lt")

    Uso en plantilla: {{ perm_type|get_permission_badge_class }}
    """
    classes = {
        "view": "bg-green-lt",
        "add": "bg-blue-lt",
        "change": "bg-orange-lt",
        "delete": "bg-red-lt",
        "other": "bg-secondary-lt",
    }
    return classes.get(perm_type, "bg-secondary-lt")


@register.filter
def get_permission_checkbox_class(perm_type):
    """
    Devuelve la clase CSS para checkboxes según el tipo de permiso.

    Args:
        perm_type (str): Tipo de permiso

    Returns:
        str: Clase CSS para el checkbox (ej: "checkbox-view")

    Uso en plantilla: {{ perm_type|get_permission_checkbox_class }}
    """
    classes = {
        "view": "checkbox-view",
        "add": "checkbox-add",
        "change": "checkbox-change",
        "delete": "checkbox-delete",
        "other": "checkbox-other",
    }
    return classes.get(perm_type, "checkbox-other")
