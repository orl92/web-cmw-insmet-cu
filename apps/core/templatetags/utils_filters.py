import re

from django import template
from django.utils.html import escape, mark_safe
from django.utils.safestring import SafeData
from django.utils.timesince import timesince
from django.utils.translation import gettext as _

register = template.Library()

_ES_MX_TRANS = str.maketrans(',.', '.,')


@register.filter(name='format_cup')
def format_cup(value):
    """Formatea un precio en CUP: `$1.234,56` (miles con `.`, decimal con `,`)."""
    if not value:
        return '$0,00'
    return f'${format(value, ",.2f").translate(_ES_MX_TRANS)}'


@register.filter
def get_dict_value(dictionary, key):
    return dictionary.get(key, '--')


@register.filter
def action_description(action_flag):
    descriptions = {
        1: 'Adición',
        2: 'Cambio',
        3: 'Eliminación',
        4: 'Inicio de Sesión',
        5: 'Cierre de Sesión',
        6: 'Modo de Mantenimiento (activado/desactivado)',
    }
    return descriptions.get(action_flag, 'Acción Desconocida')


@register.filter
def get_icon_for_action(action_flag):
    icons = {
        1: 'ti-circle-plus text-green',
        2: 'ti-edit text-orange',
        3: 'ti-trash text-red',
        4: 'ti-login-2 text-green',
        5: 'ti-logout text-red',
        6: 'ti-settings',
    }
    classes = icons.get(action_flag, 'ti-info-circle text-secondary')
    return mark_safe(f'<i class="icon ti {classes}"></i>')  # nosec B703


@register.filter
def time_since(value):
    if not value:
        return ''
    return _('hace %(timesince)s') % {'timesince': timesince(value)}


@register.filter(name='remove_images_and_special_chars')
def remove_images_and_special_chars(value):
    if not value:
        return ''
    value = re.sub(r'<img[^>]*>', '', value)
    value = re.sub(r'&nbsp;', ' ', value)
    return value


@register.filter(name='payment_method_icon')
def payment_method_icon(method):
    """Map payment method value to Tabler icon class."""
    mapping = {
        'qr': 'ti-qrcode',
        'transfer': 'ti-building-bank',
        'presencial': 'ti-building-store',
    }
    return mapping.get(method, 'ti-credit-card')


@register.filter
def get_item(dictionary, key):
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(key)


ALLOWED_TAGS = {
    'b': [],
    'strong': [],
    'i': [],
    'em': [],
    'p': [],
    'br': [],
    'ul': [],
    'ol': [],
    'li': [],
    'a': ['href'],
}

# El filtro escapa TODO primero; estas formas buscan las tags permitidas ya
# escapadas (escape() convierte `<` en `&lt;`, `>` en `&gt;` y `"` en `&quot;`)
# y las restaura como HTML real. El resto permanece escapado.
TAG_RE = re.compile(r'&lt;(/?)([a-zA-Z][a-zA-Z0-9]*)((?:\s+[a-zA-Z-]+=&quot;[^&]*&quot;)*)\s*&gt;')
ATTR_RE = re.compile(r'\s+([a-zA-Z-]+)=&quot;([^&]*)&quot;')


@register.filter
def sanitize_html(value):
    if not value:
        return value
    if isinstance(value, SafeData):
        value = str(value)
    escaped = escape(value)

    def replace_tag(m):
        closing, tag_name, attrs_str = m.group(1), m.group(2).lower(), m.group(3) or ''
        if tag_name not in ALLOWED_TAGS:
            return m.group(0)
        if closing:
            return f'</{tag_name}>'
        safe_attrs = ''
        for attr_match in ATTR_RE.finditer(attrs_str):
            attr_name, attr_val = attr_match.group(1).lower(), attr_match.group(2)
            if attr_name in ALLOWED_TAGS[tag_name]:
                safe_attrs += f' {attr_name}="{attr_val}"'
        return f'<{tag_name}{safe_attrs}>'

    result = TAG_RE.sub(replace_tag, escaped)
    return mark_safe(result)  # nosec B703
