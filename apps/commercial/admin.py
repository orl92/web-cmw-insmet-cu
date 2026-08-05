from django.contrib import admin

from apps.commercial.models import (
    Certificate,
    Contract,
    Customer,
    Invoice,
    InvoiceItem,
    Service,
    ServiceSubscription,
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'client_type', 'phone')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'service_type', 'price')


@admin.register(ServiceSubscription)
class ServiceSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'service', 'payment_status')


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    inlines = [InvoiceItemInline]
    list_display = ('number', 'customer', 'amount', 'issue_date')


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('number', 'subscription', 'date')


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'issued_date')
