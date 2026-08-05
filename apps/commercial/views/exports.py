from apps.commercial.models import (
    Certificate,
    Contract,
    Customer,
    Invoice,
    Service,
    ServiceSubscription,
)
from apps.core.views.exports import CSVExportView

_SUBSCRIPTION_STATUS = {
    'activo': 'Activo',
    'pendiente de pago': 'Pendiente de pago',
    'solicitado': 'Solicitado',
    'expirado': 'Expirado',
}


def _sub_customer(obj):
    if obj.subscription and obj.subscription.customer:
        return str(obj.subscription.customer)
    return ''


def _sub_service(obj):
    if obj.subscription and obj.subscription.service:
        return obj.subscription.service.title
    return ''


def _invoice_customer(invoice):
    if invoice.subscription and invoice.subscription.customer:
        return str(invoice.subscription.customer)
    if invoice.customer:
        return str(invoice.customer)
    item = (
        invoice.items.filter(subscription__isnull=False)
        .select_related('subscription__customer')
        .first()
    )
    if item and item.subscription and item.subscription.customer:
        return str(item.subscription.customer)
    return ''


def _invoice_services(invoice):
    if invoice.subscription and invoice.subscription.service:
        return invoice.subscription.service.title
    titles = []
    for item in invoice.items.all():
        if item.subscription and item.subscription.service:
            titles.append(item.subscription.service.title)
        elif item.descripcion:
            titles.append(item.descripcion)
    return '; '.join(dict.fromkeys(titles))


class CustomerCSVExportView(CSVExportView):
    model = Customer
    permission_required = 'commercial.view_customer'
    filename = 'clientes.csv'
    columns = [
        ('Cliente', lambda o: str(o)),
        ('Tipo de Cliente', lambda o: o.get_client_type_display()),
        (
            'Identificación',
            lambda o: (
                f'REEUP {o.reeup} / NIT {o.nit}'
                if o.client_type == Customer.ClientType.JURIDICA
                else ''
            ),
        ),
        ('Cuenta Bancaria', 'account'),
        ('Agencia Bancaria', 'agency_bank'),
        ('Correo Electrónico', lambda o: o.user.email or ''),
        ('Teléfono', 'phone'),
        ('Dirección', 'address'),
        ('Registro Activo', lambda o: 'Sí' if o.record_active else 'No'),
    ]


class ServiceCSVExportView(CSVExportView):
    model = Service
    permission_required = 'commercial.view_service'
    filename = 'servicios.csv'
    columns = [
        ('Título', 'title'),
        ('Código', 'code'),
        ('Tipo', lambda o: o.get_service_type_display()),
        ('Precio (CUP/día)', 'price'),
        ('Fecha', lambda o: o.date.strftime('%d/%m/%Y %H:%M') if o.date else ''),
        ('Usuario', lambda o: o.user.get_full_name() or o.user.username),
        ('Suscripciones', lambda o: str(o.servicesubscription_set.count())),
        ('Resumen', 'summary'),
        ('Registro Activo', lambda o: 'Sí' if o.record_active else 'No'),
    ]


class ServiceSubscriptionCSVExportView(CSVExportView):
    model = ServiceSubscription
    permission_required = 'commercial.view_subscription'
    filename = 'suscripciones.csv'
    columns = [
        ('Cliente', lambda o: str(o.customer) if o.customer else ''),
        ('Servicio', lambda o: o.service.title if o.service else ''),
        ('Inicio', lambda o: o.start_date.strftime('%d/%m/%Y %H:%M') if o.start_date else ''),
        ('Expiración', lambda o: o.end_date.strftime('%d/%m/%Y %H:%M') if o.end_date else ''),
        ('Estado', lambda o: _SUBSCRIPTION_STATUS.get(o.status_display, o.status_display.title())),
        ('Pago', lambda o: o.get_payment_status_display()),
        ('Método de Pago', lambda o: o.get_payment_method_display() if o.payment_method else ''),
        ('Registro Activo', lambda o: 'Sí' if o.record_active else 'No'),
    ]


class InvoiceCSVExportView(CSVExportView):
    model = Invoice
    permission_required = 'commercial.view_invoice'
    filename = 'facturas.csv'
    columns = [
        ('Número', 'number'),
        ('Fecha', lambda o: o.issue_date.strftime('%d/%m/%Y %H:%M') if o.issue_date else ''),
        ('Cliente', _invoice_customer),
        ('Servicio(s)', _invoice_services),
        ('Monto', 'amount'),
        ('Estado', lambda o: 'Anulada' if o.is_cancelled else 'Activa'),
        ('Correo Enviado', lambda o: 'Sí' if o.email_sent else 'No'),
    ]


class ContractCSVExportView(CSVExportView):
    model = Contract
    permission_required = 'commercial.view_contract'
    filename = 'contratos.csv'
    columns = [
        ('Número', 'number'),
        ('Cliente', _sub_customer),
        ('Servicio', _sub_service),
        ('Fecha', lambda o: o.date.strftime('%d/%m/%Y') if o.date else ''),
        ('Registro Comercial', 'commercial_registry'),
        ('Pago', lambda o: o.subscription.get_payment_status_display() if o.subscription else ''),
        ('Activo', lambda o: 'Sí' if o.record_active else 'No'),
    ]


class CertificateCSVExportView(CSVExportView):
    model = Certificate
    permission_required = 'commercial.view_certificate'
    filename = 'certificados.csv'
    columns = [
        ('Cliente', _sub_customer),
        ('Servicio', _sub_service),
        (
            'Fecha Emisión',
            lambda o: o.issued_date.strftime('%d/%m/%Y %H:%M') if o.issued_date else '',
        ),
        ('Pago', lambda o: o.subscription.get_payment_status_display() if o.subscription else ''),
        ('Activo', lambda o: 'Sí' if o.record_active else 'No'),
    ]
