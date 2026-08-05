import math

from django import template

from apps.core.models import CODIGOS_SIN_VARIACION, TIEMPO_IMG_BASE_MAP

register = template.Library()

WEATHER_DESCRIPTIONS = {
    'despejado': 'Despejado',
    'mayormente_despejado': 'Mayormente despejado',
    'parcialmente_nublado': 'Parcialmente nublado',
    'mayormente_nublado': 'Mayormente nublado',
    'nublado': 'Nublado',
    'lluvias': 'Lluvias',
    'lluvias_debiles': 'Lluvias débiles',
    'chubascos': 'Chubascos',
    'chubascos_electricos': 'Chubascos eléctricos',
    'chubascos_lluvias': 'Chubascos y lluvias',
    'tormenta': 'Tormenta eléctrica',
}

MOON_DESCRIPTIONS = {
    'nueva': 'Luna nueva',
    'creciente': 'Luna creciente',
    'cuarto_creciente': 'Cuarto creciente',
    'creciente_gibosa': 'Creciente gibosa',
    'llena': 'Luna llena',
    'menguante_gibosa': 'Menguante gibosa',
    'cuarto_menguante': 'Cuarto menguante',
    'menguante': 'Luna menguante',
}

SUN_DESCRIPTIONS = {
    'amanecer': 'Amanecer',
    'atardecer': 'Atardecer',
}

MAR_DESCRIPTIONS = {
    'TQ': 'Tranquila',
    'PO': 'Poco Oleaje',
    'O': 'Oleaje',
    'MRJ': 'Marejadas',
    'FMRJ': 'Fuertes Marejadas',
}

PERIOD_NAMES = {
    'noche': 'Noche',
    'madrugada': 'Madrugada',
    'manana': 'Mañana',
    'tarde': 'Tarde',
}

PERIOD_ORDER = {'noche': 0, 'madrugada': 1, 'manana': 2, 'tarde': 3}


@register.filter
def weather_description(code):
    return WEATHER_DESCRIPTIONS.get(code, code)


@register.filter
def mar_description(code):
    return MAR_DESCRIPTIONS.get(code, code)


@register.filter
def moon_description(code):
    return MOON_DESCRIPTIONS.get(code, code)


@register.filter
def sun_description(code):
    return SUN_DESCRIPTIONS.get(code, code)


@register.filter
def period_name(code):
    return PERIOD_NAMES.get(code, code)


@register.filter
def weather_img(code, period=''):
    base = TIEMPO_IMG_BASE_MAP.get(code, 'default')
    if period:
        period = period.lower()
        if period in CODIGOS_SIN_VARIACION or code in ('noche', 'madrugada'):
            return f'dist/img/weather_icon/{base}.png'
        if period in ('noche', 'madrugada'):
            return (
                f'dist/img/weather_icon/{base}_noche.png'
                if code in ('despejado', 'mayormente_despejado')
                else f'dist/img/weather_icon/{base}.png'
            )
        return f'dist/img/weather_icon/{base}.png'
    return f'dist/img/weather_icon/{base}.png'


@register.filter
def moon_img(phase):
    return f'dist/img/weather_icon/luna_{phase}.png'


@register.filter
def sun_img(event):
    return f'dist/img/weather_icon/{event}.png'


@register.filter
def get_forecast_day(forecast, day_number):
    day = forecast.extended_forecast.filter(day_number=day_number).first()
    if day is None:
        return {}
    return {
        'date': day.date,
        'weather': day.weather,
        'max_temp': day.max_temp,
        'min_temp': day.min_temp,
    }


@register.filter
def get_period(forecast, period):
    return forecast.north.filter(period=period).first()


@register.filter
def sort_periods(regions):
    return sorted(regions, key=lambda r: PERIOD_ORDER.get(r.period, 99))


register.filter('get_tiempo_description', weather_description)
register.filter('get_mar_description', mar_description)
register.filter('get_luna_description', moon_description)
register.filter('get_sol_description', sun_description)
register.filter('get_weather_img', weather_img)
register.filter('get_moon_img', moon_img)
register.filter('get_sun_img', sun_img)
register.filter('get_period_name', period_name)
register.filter('period_display', period_name)


@register.filter
def uv_cx(uv_index):
    uv = min(int(uv_index), 11)
    angle_deg = 120.9 + uv * 24.1
    cx = 90.5 + 76 * math.cos(math.radians(angle_deg))
    return f'{cx:.1f}'


@register.filter
def uv_cy(uv_index):
    uv = min(int(uv_index), 11)
    angle_deg = 120.9 + uv * 24.1
    cy = 80 + 76 * math.sin(math.radians(angle_deg))
    return f'{cy:.1f}'


@register.filter
def uv_color(uv_index):
    uv = int(uv_index)
    if uv <= 2:
        return '#73AA24'
    elif uv <= 5:
        return '#FDE300'
    elif uv <= 7:
        return '#FF8C00'
    elif uv <= 10:
        return '#D13438'
    else:
        return '#5C2E91'
