import math

from django import template

register = template.Library()

@register.filter
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

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
