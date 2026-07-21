import os

from django import template

register = template.Library()


@register.filter(name="add_class")
def add_class(value, arg):
    return value.as_widget(attrs={"class": arg})


@register.filter(name="add_attrs")
def add_attrs(field, attrs):
    attrs = attrs.split(",")
    attrs_dict = {
        attr.split(":")[0].strip(): attr.split(":")[1].strip() for attr in attrs
    }
    return field.as_widget(attrs=attrs_dict)


@register.filter
def filename(value):
    return os.path.splitext(os.path.basename(value))[0]
