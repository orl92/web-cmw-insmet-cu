from django.contrib import admin
from apps.core.models import SiteConfiguration, CompanySettings, EmailRecipientList, EmailRecipient

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ('maintenance_mode',)

@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_reeup', 'nit')

class EmailRecipientInline(admin.TabularInline):
    model = EmailRecipient
    extra = 1

@admin.register(EmailRecipientList)
class EmailRecipientListAdmin(admin.ModelAdmin):
    inlines = [EmailRecipientInline]
    list_display = ('name',)
