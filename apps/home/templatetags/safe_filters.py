import re

from django import template
from django.utils.html import escape, mark_safe
from django.utils.safestring import SafeData

register = template.Library()

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
