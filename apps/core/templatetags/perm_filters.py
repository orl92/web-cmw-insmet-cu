from collections import defaultdict

from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter
def has_permission(user, perm):
    return user.has_perm(perm)


@register.filter
def group_permissions(user):
    if user.is_superuser:
        return []
    perms = set()
    for group in user.groups.all():
        for perm in group.permissions.all():
            perms.add(perm)
    return sorted(perms, key=lambda p: p.name)


@register.filter
def user_permissions(user):
    if user.is_superuser:
        return []
    return sorted(user.user_permissions.all(), key=lambda p: p.name)


@register.simple_tag
def if_group(user, group_name, content=''):
    if user.groups.filter(name=group_name).exists():
        return content
    return ''


@register.filter
def can(permission_required, user):
    if user.is_superuser:
        return True
    codename = (
        permission_required.split('.')[-1] if '.' in permission_required else permission_required
    )
    for group in user.groups.all():
        for perm in group.permissions.all():
            if perm.codename == codename:
                return True
    return user.user_permissions.filter(codename=codename).exists()


@register.filter
def filter_permissions(permissions, app_name):
    return [p for p in permissions if p.content_type.app_label == app_name]


@register.filter
def get_model_verbose_name(permission):
    try:
        model_class = permission.content_type.model_class()
        if model_class:
            return model_class._meta.verbose_name
    except AttributeError, TypeError:
        pass
    return permission.content_type.model.replace('_', ' ').title()


@register.filter
def get_permission_type_from_codename(permission):
    codename = permission.codename.lower()
    if codename.startswith('view_'):
        return 'view'
    elif codename.startswith('add_'):
        return 'add'
    elif codename.startswith('change_'):
        return 'change'
    elif codename.startswith('delete_'):
        return 'delete'
    else:
        return 'other'


@register.filter
def filter_permissions_by_type(permissions, perm_type):
    return [p for p in permissions if get_permission_type_from_codename(p) == perm_type]


@register.filter
def group_permissions_for_table(permissions):
    grouped = defaultdict(lambda: {'view': None, 'add': None, 'change': None, 'delete': None})
    for perm in permissions:
        model_name = get_model_verbose_name(perm)
        perm_type = get_permission_type_from_codename(perm)
        if perm_type in ['view', 'add', 'change', 'delete']:
            grouped[model_name][perm_type] = {
                'perm': perm,
                'field_name': 'permissions',
                'field_id': f'perm_{perm.id}',
                'is_checked': False,
            }
    return dict(sorted(grouped.items()))


@register.filter
def group_permissions_for_modal(permissions):
    grouped = defaultdict(
        lambda: defaultdict(lambda: {'view': False, 'add': False, 'change': False, 'delete': False})
    )
    for perm in permissions:
        app_label = perm.content_type.app_label
        model_display_name = get_model_verbose_name(perm)
        perm_type = get_permission_type_from_codename(perm)
        if perm_type in ['view', 'add', 'change', 'delete']:
            grouped[app_label][model_display_name][perm_type] = True

    result = []
    for app_label in sorted(grouped.keys()):
        models = []
        for model_display_name, perms in grouped[app_label].items():
            models.append({'name': model_display_name, 'permissions': perms})
        result.append({'app_label': app_label, 'models': sorted(models, key=lambda x: x['name'])})
    return result


@register.filter
def get_permission_verb(perm_type):
    verbs = {
        'view': 'Ver',
        'add': 'Añadir',
        'change': 'Editar',
        'delete': 'Eliminar',
        'other': 'Otro',
    }
    return verbs.get(perm_type, 'Otro')


@register.filter
def get_permission_badge_class(perm_type):
    classes = {
        'view': 'bg-green-lt',
        'add': 'bg-blue-lt',
        'change': 'bg-orange-lt',
        'delete': 'bg-red-lt',
        'other': 'bg-secondary-lt',
    }
    return classes.get(perm_type, 'bg-secondary-lt')


@register.filter
def get_permission_checkbox_class(perm_type):
    classes = {
        'view': 'checkbox-view',
        'add': 'checkbox-add',
        'change': 'checkbox-change',
        'delete': 'checkbox-delete',
        'other': 'checkbox-other',
    }
    return classes.get(perm_type, 'checkbox-other')
