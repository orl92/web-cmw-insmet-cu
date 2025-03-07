from django.contrib import admin

from dashboard.models import *

# Register your models here.

@admin.register(Forecasts)
class ForecastsAdmin(admin.ModelAdmin):
    list_display = ('date',)
    list_filter = ('date',)

@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'number', 'latitude', 'longitude', 'province')
    list_filter = ('province',)
    search_fields = ('name',)

@admin.register(EarlyWarning)
class EarlyWarningAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'user')

@admin.register(TropicalCyclone)
class TropicalCycloneAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'user')

@admin.register(SpecialNotice)
class SpecialNoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'user')

@admin.register(RadarWarning)
class RadarWarningAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'user')

@admin.register(Service)
class ServicesAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'user')
    
class EmailRecipientInline(admin.TabularInline):
    model = EmailRecipient
    extra = 1

@admin.register(EmailRecipientList)
class EmailRecipientListAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    inlines = [EmailRecipientInline]
