import re

from django import template
from django.utils.html import escape, mark_safe
from django.utils.safestring import SafeData
from django.utils.timesince import timesince
from django.utils.translation import gettext as _

register = template.Library()


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


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


ALLOWED_TAGS = {
    'b': [], 'strong': [], 'i': [], 'em': [], 'p': [],
    'br': [], 'ul': [], 'ol': [], 'li': [],
    'a': ['href'],
}

TAG_RE = re.compile(r'</?(\w+)([^>]*)>', re.IGNORECASE)
ATTR_RE = re.compile(r'\s*(\w+)\s*=\s*"([^"]*)"')


@register.filter
def sanitize_html(value):
    if not value:
        return value
    if isinstance(value, SafeData):
        value = str(value)
    escaped = escape(value)
    def replace_tag(m):
        tag_name = m.group(1).lower()
        if tag_name not in ALLOWED_TAGS:
            return ''
        attrs_str = m.group(2)
        if m.group(0).startswith('</'):
            return f'</{tag_name}>'
        allowed_attrs = ALLOWED_TAGS[tag_name]
        safe_attrs = ''
        if attrs_str:
            for attr_match in ATTR_RE.finditer(attrs_str):
                attr_name = attr_match.group(1).lower()
                attr_val = attr_match.group(2)
                if attr_name in allowed_attrs:
                    safe_attrs += f' {attr_name}="{escape(attr_val)}"'
        return f'<{tag_name}{safe_attrs}>'
    result = TAG_RE.sub(replace_tag, escaped)
    return mark_safe(result)
