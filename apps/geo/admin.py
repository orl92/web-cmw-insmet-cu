from django.contrib import admin

from apps.geo.models import Province, Station


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'number', 'latitude', 'longitude', 'province')
    list_filter = ('province',)
    search_fields = ('name',)
