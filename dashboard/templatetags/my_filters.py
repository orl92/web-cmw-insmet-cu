from django import template

from . import form_filters, meteo_filters, perm_filters, utils_filters

register = template.Library()

for mod in (form_filters, meteo_filters, perm_filters, utils_filters):
    register.filters.update(mod.register.filters)
