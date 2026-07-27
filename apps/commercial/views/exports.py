from apps.commercial.models import (
    Certificate,
    Contract,
    Customer,
    Invoice,
    Service,
    ServiceSubscription,
)
from apps.core.views.exports import CSVExportView


class CustomerCSVExportView(CSVExportView):
    model = Customer
    permission_required = 'commercial.view_customer'
    filename = 'clientes.csv'
    columns = [
        ('Empresa', 'company_name'),
        ('REEUP', 'reeup'),
        ('NIT', 'nit'),
        ('Cuenta Bancaria', 'account'),
        ('Teléfono', 'phone'),
        ('Dirección', 'address'),
        ('Email', lambda o: o.user.email if o.user else ''),
        ('Registro Activo', lambda o: 'Sí' if o.record_active else 'No'),
    ]


class ServiceCSVExportView(CSVExportView):
    model = Service
    permission_required = 'commercial.view_service'
    filename = 'servicios.csv'
    columns = [
        ('Título', 'title'),
        ('Precio', 'price'),
        ('Tipo', lambda o: o.get_service_type_display()),
        ('Resumen', 'summary'),
        ('Registro Activo', lambda o: 'Sí' if o.record_active else 'No'),
    ]


class ServiceSubscriptionCSVExportView(CSVExportView):
    model = ServiceSubscription
    permission_required = 'commercial.view_subscription'
    filename = 'suscripciones.csv'
    columns = [
        ('Cliente', lambda o: o.customer.company_name if o.customer else ''),
        ('Servicio', lambda o: o.service.title if o.service else ''),
        ('Inicio', lambda o: o.start_date.isoformat() if o.start_date else ''),
        ('Fin', lambda o: o.end_date.isoformat() if o.end_date else ''),
        ('Estado Pago', lambda o: o.get_payment_status_display()),
        ('Registro Activo', lambda o: 'Sí' if o.record_active else 'No'),
    ]


class InvoiceCSVExportView(CSVExportView):
    model = Invoice
    permission_required = 'commercial.view_invoice'
    filename = 'facturas.csv'
    columns = [
        ('Número', 'number'),
        ('Fecha', lambda o: o.issue_date.isoformat() if o.issue_date else ''),
        ('Cliente', lambda o: o.subscription.customer.company_name if o.subscription and o.subscription.customer else o.customer.company_name if o.customer else ''),
        ('Monto', 'amount'),
        ('Anulada', lambda o: 'Sí' if o.is_cancelled else 'No'),
        ('Correo Enviado', lambda o: 'Sí' if o.email_sent else 'No'),
    ]


class ContractCSVExportView(CSVExportView):
    model = Contract
    permission_required = 'commercial.view_contract'
    filename = 'contratos.csv'
    columns = [
        ('Número', 'number'),
        ('Cliente', lambda o: o.subscription.customer.company_name if o.subscription and o.subscription.customer else ''),
        ('Servicio', lambda o: o.subscription.service.title if o.subscription and o.subscription.service else ''),
        ('Fecha', lambda o: o.date.isoformat() if o.date else ''),
        ('Registro Comercial', 'commercial_registry'),
        ('Activo', lambda o: 'Sí' if o.record_active else 'No'),
    ]


class CertificateCSVExportView(CSVExportView):
    model = Certificate
    permission_required = 'commercial.view_certificate'
    filename = 'certificados.csv'
    columns = [
        ('Cliente', lambda o: o.subscription.customer.company_name if o.subscription and o.subscription.customer else ''),
        ('Servicio', lambda o: o.subscription.service.title if o.subscription and o.subscription.service else ''),
        ('Fecha Emisión', lambda o: o.issued_date.isoformat() if o.issued_date else ''),
        ('Activo', lambda o: 'Sí' if o.record_active else 'No'),
    ]
