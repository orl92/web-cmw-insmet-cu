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
    return value.name.split('/')[-1] if value else ''
