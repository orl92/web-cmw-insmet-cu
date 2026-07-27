from django.contrib import admin
from apps.meteo.models import Forecasts, ForecastRegions, ForecastExtendedDay, WeatherReport, Province, Town, Station, Warning

class ForecastRegionsInline(admin.TabularInline):
    model = ForecastRegions
    extra = 3

class ForecastExtendedDayInline(admin.TabularInline):
    model = ForecastExtendedDay
    extra = 5

@admin.register(Forecasts)
class ForecastsAdmin(admin.ModelAdmin):
    inlines = [ForecastRegionsInline, ForecastExtendedDayInline]
    list_display = ('date', 'sunrise', 'sunset', 'uv_index')

@admin.register(WeatherReport)
class WeatherReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'date', 'user')
    list_filter = ('report_type',)


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')


@admin.register(Town)
class TownAdmin(admin.ModelAdmin):
    list_display = ('name', 'province')
    list_filter = ('province',)
    search_fields = ('name',)


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'number', 'latitude', 'longitude', 'province')
    list_filter = ('province',)
    search_fields = ('name',)


@admin.register(Warning)
class WarningAdmin(admin.ModelAdmin):
    list_display = ('warning_type', 'summary', 'date', 'user')
    list_filter = ('warning_type',)
    search_fields = ('summary',)
