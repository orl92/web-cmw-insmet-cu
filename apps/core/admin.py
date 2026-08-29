from django.contrib import admin

from apps.core.models import (
    ActivityLog,
    CompanySettings,
    EmailRecipient,
    EmailRecipientList,
    SiteConfiguration,
    TaskExecutionLog,
)


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


@admin.register(TaskExecutionLog)
class TaskExecutionLogAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'status', 'attempts', 'enqueued_at', 'finished_at')
    list_filter = ('status',)
    readonly_fields = [f.name for f in TaskExecutionLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'action_flag', 'object_repr')
    list_filter = ('user', 'action_flag', 'action_time')
    search_fields = ('object_repr', 'message', 'ip_address')
    readonly_fields = [f.name for f in ActivityLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
