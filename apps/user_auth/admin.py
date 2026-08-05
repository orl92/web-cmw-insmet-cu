from django.contrib import admin

from apps.user_auth.models import GroupProfile, PermissionProfile, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_ldap', 'newsletter')


@admin.register(GroupProfile)
class GroupProfileAdmin(admin.ModelAdmin):
    list_display = ('group',)


@admin.register(PermissionProfile)
class PermissionProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'permissions_count')
    filter_horizontal = ('permissions',)

    def permissions_count(self, obj):
        return obj.permissions.count()

    permissions_count.short_description = 'Permisos'
