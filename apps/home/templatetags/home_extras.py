from django import template

register = template.Library()

@register.filter
def has_group(user, group_name):
    """
    Verifica si un usuario pertenece a un grupo específico.
    Uso en templates: {% if user|has_group:'Clientes' %}
    """
    return user.groups.filter(name=group_name).exists()

@register.filter
def get_item(dictionary, key):
    """
    Obtiene un valor de un diccionario usando una clave.
    Uso en templates: {{ user_subscriptions|get_item:service.id }}
    """
    return dictionary.get(key)
