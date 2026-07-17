from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils import timezone

from common.views import CSVExportView
from dashboard.models import (
    Customer,
    EarlyWarning,
    Forecasts,
    Invoice,
    Service,
    ServiceSubscription,
    StormWarning,
    TropicalCyclone,
    WeatherReport,
)


class CustomerCSVExportView(CSVExportView):
    model = Customer
    permission_required = 'dashboard.view_customer'
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
    permission_required = 'dashboard.view_service'
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
    permission_required = 'dashboard.view_subscription'
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
    permission_required = 'dashboard.view_invoice'
    filename = 'facturas.csv'
    columns = [
        ('Número', 'number'),
        ('Fecha', lambda o: o.issue_date.isoformat() if o.issue_date else ''),
        ('Cliente', lambda o: o.subscription.customer.company_name if o.subscription and o.subscription.customer else o.customer.company_name if o.customer else ''),
        ('Monto', 'amount'),
        ('Anulada', lambda o: 'Sí' if o.is_cancelled else 'No'),
        ('Correo Enviado', lambda o: 'Sí' if o.email_sent else 'No'),
    ]


class ForecastsCSVExportView(CSVExportView):
    model = Forecasts
    permission_required = 'dashboard.view_forecast'
    filename = 'pronosticos.csv'
    columns = [
        ('Fecha', lambda o: o.date.isoformat() if o.date else ''),
        ('Creado', lambda o: o.created_at.isoformat() if hasattr(o, 'created_at') and o.created_at else ''),
    ]


class WeatherReportCSVExportView(CSVExportView):
    model = WeatherReport
    permission_required = 'dashboard.view_forecast'
    filename = 'reportes_tiempo.csv'
    columns = [
        ('Tipo', lambda o: o.get_type_display()),
        ('Fecha', lambda o: o.date.isoformat() if o.date else ''),
        ('Hora', lambda o: o.time.isoformat() if hasattr(o, 'time') and o.time else ''),
        ('Autor', lambda o: o.author.username if o.author else ''),
        ('Creado', lambda o: o.created_at.isoformat() if hasattr(o, 'created_at') and o.created_at else ''),
    ]


class EarlyWarningCSVExportView(CSVExportView):
    model = EarlyWarning
    permission_required = 'dashboard.view_early_warning'
    filename = 'alertas_tempranas.csv'
    columns = [
        ('Resumen', 'summary'),
        ('Fecha', lambda o: o.date.isoformat() if o.date else ''),
        ('Válido Hasta', lambda o: o.valid_until.isoformat() if hasattr(o, 'valid_until') and o.valid_until else ''),
        ('Usuario', lambda o: o.user.username if o.user else ''),
    ]


class TropicalCycloneCSVExportView(CSVExportView):
    model = TropicalCyclone
    permission_required = 'dashboard.view_tropical_cyclone'
    filename = 'ciclones_tropicales.csv'
    columns = [
        ('Resumen', 'summary'),
        ('Fecha', lambda o: o.date.isoformat() if o.date else ''),
        ('Válido Hasta', lambda o: o.valid_until.isoformat() if hasattr(o, 'valid_until') and o.valid_until else ''),
        ('Usuario', lambda o: o.user.username if o.user else ''),
    ]


class StormWarningCSVExportView(CSVExportView):
    model = StormWarning
    permission_required = 'dashboard.view_storm_warning'
    filename = 'avisos_tormentas.csv'
    columns = [
        ('Resumen', 'summary'),
        ('Fecha', lambda o: o.date.isoformat() if o.date else ''),
        ('Válido Hasta', lambda o: o.valid_until.isoformat() if hasattr(o, 'valid_until') and o.valid_until else ''),
        ('Usuario', lambda o: o.user.username if o.user else ''),
    ]
