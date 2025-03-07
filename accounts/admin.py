from django.contrib import admin

from accounts.models import GroupProfile, Profile

# Register your models here.

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'avatar')

@admin.register(GroupProfile)
class GroupProfileAdmin(admin.ModelAdmin):
    list_display = ['group']