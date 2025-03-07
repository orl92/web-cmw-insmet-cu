from django.contrib import admin

from home.models import Maps

# Register your models here.

@admin.register(Maps)
class MapsAdmin(admin.ModelAdmin):
    list_display = ('hour', 'type', 'image')