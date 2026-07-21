from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.templatetags.static import static

from common.utils import get_img_path

register = template.Library()


@register.filter
def get_tiempo_description(value):
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
    SOL_DESCRIPCIONES = {
        "sunrise": "Hora oficial de salida del sol",
        "sunset": "Hora oficial de puesta del sol",
    }
    return SOL_DESCRIPCIONES.get(value, "Descripción no disponible")


@register.filter
def get_weather_img_morning(weather_code):
    return get_img_path(weather_code, "morning")


@register.filter
def get_weather_img_afternoon(weather_code):
    return get_img_path(weather_code, "afternoon")


@register.filter
def get_weather_img_night(weather_code):
    return get_img_path(weather_code, "night")


@register.filter
def get_weather_img(weather_code, period="afternoon"):
    return get_img_path(weather_code, period)


@register.filter
def get_moon_img(moon_phase):
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
    SUN_IMG_MAP = {
        "sunrise": "dist/img/sun/sunrise.png",
        "sunset": "dist/img/sun/sunset.png",
    }
    return static(SUN_IMG_MAP.get(sun_event, ""))


@register.filter
def get_forecast_day(obj, day_number):
    if hasattr(obj, 'extended_days'):
        try:
            day = obj.extended_days.get(day_number=day_number)
            return {
                "date": day.date,
                "weather": day.weather,
                "max_temp": day.max_temp,
                "min_temp": day.min_temp,
            }
        except (ObjectDoesNotExist, AttributeError):
            pass
    day_str = str(day_number)
    return {
        "date": getattr(obj, f"day{day_str}_date", "--"),
        "weather": getattr(obj, f"day{day_str}_weather", "--"),
        "max_temp": getattr(obj, f"day{day_str}_max_temp", "--"),
        "min_temp": getattr(obj, f"day{day_str}_min_temp", "--"),
    }


@register.filter
def period_display(value):
    mapping = {'morning': 'Mañana', 'afternoon': 'Tarde', 'night': 'Noche'}
    return mapping.get(value, value or '')
