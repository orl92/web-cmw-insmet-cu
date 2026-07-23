from django.contrib import admin

from apps.crm.models import Customer, Service, ServiceSubscription


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'client_type', 'phone', 'user')
    search_fields = ('company_name', 'phone', 'user__username')
    ordering = ('company_name',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'service_type', 'price', 'date')
    list_filter = ('service_type',)
    search_fields = ('title', 'code')
    ordering = ('-date',)


@admin.register(ServiceSubscription)
class ServiceSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'service', 'payment_status', 'start_date', 'end_date')
    list_filter = ('payment_status', 'payment_method')
    search_fields = ('customer__company_name', 'service__title')
    ordering = ('-start_date',)
