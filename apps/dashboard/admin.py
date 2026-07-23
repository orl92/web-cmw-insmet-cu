from django.contrib import admin

from apps.dashboard.models import (
    EarlyWarning,
    EmailRecipient,
    EmailRecipientList,
    Forecasts,
    Service,
    StormWarning,
    TropicalCyclone,
    WeatherReport,
)


@admin.register(Forecasts)
class ForecastsAdmin(admin.ModelAdmin):
    list_display = ('date',)
    list_filter = ('date',)

@admin.register(EarlyWarning)
class EarlyWarningAdmin(admin.ModelAdmin):
    list_display = ('summary', 'date', 'user')

@admin.register(TropicalCyclone)
class TropicalCycloneAdmin(admin.ModelAdmin):
    list_display = ('summary', 'date', 'user')

@admin.register(StormWarning)
class StormWarningAdmin(admin.ModelAdmin):
    list_display = ('summary', 'date', 'user')

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

@admin.register(WeatherReport)
class WeatherReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'summary', 'date', 'user', 'email_recipient_list')
    list_filter = ('report_type', 'date')
    search_fields = ('summary',)
    date_hierarchy = 'date'
    radio_fields = {'report_type': admin.VERTICAL}
    autocomplete_fields = ['user', 'email_recipient_list']
    fieldsets = (
        (None, {
            'fields': ('report_type', 'user', 'date')
        }),
        ('Contenido', {
            'fields': ('summary', 'content', 'file')
        }),
        ('Distribución', {
            'fields': ('email_recipient_list',),
            'classes': ('collapse',)
        }),
    )
