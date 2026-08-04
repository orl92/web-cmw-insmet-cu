import re
from datetime import date, datetime

from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value, css_class):
    return value.as_widget(attrs={'class': css_class})

@register.filter(name='add_attrs')
def add_attrs(value, attrs_str):
    pairs = attrs_str.split(',')
    attrs = {}
    for pair in pairs:
        key, val = pair.split(':', 1)
        attrs[key.strip()] = val.strip()
    return value.as_widget(attrs=attrs)

@register.filter
def filename(value):
    if not value:
        return ''
    name = value.name.split('/')[-1]
    return re.sub(r'^[0-9a-f-]{36}_', '', name)

@register.filter
def iso_date(value):
    if isinstance(value, date):
        return value.strftime('%Y-%m-%d')
    return value

@register.filter
def iso_datetime(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%dT%H:%M')
    return value
