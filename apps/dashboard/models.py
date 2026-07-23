import re
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from apps.common.utils import (
    FileHandlerMixin,
    SoftDeleteModel,
    image_upload_path,
    pdf_upload_path,
)
from apps.crm.models import Customer, Service, ServiceSubscription
from apps.geo.models import Province, Town, Station


class SiteConfiguration(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    maintenance_mode = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Configuración del Sitio"
        verbose_name_plural = "Configuraciones del Sitio"
        default_permissions = ()
        permissions = (
            ("view_site_configuration", "Ver"),
            ("add_site_configuration", "Añadir"),
            ("change_site_configuration", "Editar"),
            ("delete_site_configuration", "Eliminar"),
        )
        ordering = ('-id',)

    def __str__(self):
        return f"Modo Mantenimiento: {'Activado' if self.maintenance_mode else 'Desactivado'}"


def validate_telefonos(value):
    """Valida que el campo contenga una lista de números de 8 dígitos separados por comas."""
    if not value.strip():
        return  # permitir vacío si se desea, o puedes lanzar error si es obligatorio
    numeros = [num.strip() for num in value.split(',') if num.strip()]
    for num in numeros:
        if not re.match(r'^\d{8}$', num):
            raise ValidationError(
                'Cada número de teléfono debe tener 8 dígitos. Separe varios números con comas.'
            )


class CompanySettings(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    # --- Validadores ---
    reeup_validator = RegexValidator(
        regex=r'^\d{3}\.\d{1,2}\.\d{4,5}$',
        message='El REEUP debe tener el formato ###.#.####, ###.#.#####, ###.##.#### o ###.##.#####.'
    )
    nit_validator = RegexValidator(
        regex=r'^\d{11}$',
        message='El NIT debe estar compuesto por 11 dígitos numéricos.'
    )
    cuenta_validator = RegexValidator(
        regex=r'^\d{16}$',
        message='La cuenta bancaria debe tener 16 dígitos numéricos.'
    )

    # --- Campos ---
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la empresa")
    direccion = models.CharField(max_length=200, verbose_name="Dirección")
    codigo_reeup = models.CharField(
        max_length=12,
        validators=[reeup_validator],
        unique=True,
        verbose_name="Código REEUP"
    )
    nit = models.CharField(
        max_length=11,
        validators=[nit_validator],
        unique=True,
        verbose_name="NIT"
    )
    cuenta_bancaria = models.CharField(
        max_length=16,
        validators=[cuenta_validator],
        verbose_name="Cuenta bancaria"
    )
    agencia_bancaria = models.CharField(max_length=100, verbose_name="Agencia bancaria")
    telefonos = models.CharField(
        max_length=100,
        validators=[validate_telefonos],
        verbose_name="Teléfonos",
        help_text="Ingrese uno o más números de 8 dígitos separados por comas."
    )
    registro_comercial = models.CharField(max_length=50, verbose_name="Registro comercial")

    class Meta:
        verbose_name = 'Configuración de la empresa'
        verbose_name_plural = verbose_name
        default_permissions = ()
        permissions = (
            ("view_company_settings", "Ver"),
            ("add_company_settings", "Añadir"),
            ("change_company_settings", "Editar"),
            ("delete_company_settings", "Eliminar"),
        )
        ordering = ('-id',)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        obj, created = cls.objects.get_or_create()
        return obj


class Forecasts(models.Model):
    TIEMPO_CHOICES = [
        ("PN", "PN"),  # Poco Nublado
        ("PARCN", "PARCN"),  # Parcialmente Nublado
        ("N", "N"),  # Nublado
        ("AIS CHUB", "AIS CHUB"),  # Aislados Chubascos
        ("ALG CHUB", "ALG CHUB"),  # Algunos Chubascos
        ("NUM CHUB", "NUM CHUB"),  # Numerosos Chubascos
        ("ALG TORM", "ALG TORM"),  # Algunas Tormentas
        ("NUM TORM", "NUM TORM"),  # Numerosas Tormentas
    ]

    VIENTO_DIRECCION_CHOICES = [
        ("VRB", "VRB"),  # Variable Debil
        ("N", "N"),  # Norte
        ("NNE", "NNE"),  # Norte Noreste
        ("NE", "NE"),  # Noreste
        ("ENE", "ENE"),  # Este Noreste
        ("E", "E"),  # Este
        ("ESE", "ESE"),  # Este Sureste
        ("SE", "SE"),  # Sureste
        ("SSE", "SSE"),  # Sur Sureste
        ("S", "S"),  # Sur
        ("SSW", "SSW"),  # Sur Suroeste
        ("SW", "SW"),  # Suroeste
        ("WSW", "WSW"),  # Oeste Suroeste
        ("W", "W"),  # Oeste
        ("WNW", "WNW"),  # Oeste Noroeste
        ("NW", "NW"),  # Noroeste
        ("NNW", "NNW"),  # Norte Noroeste
    ]

    LUNA_CHOICES = [
        ("Luna Nueva", "Luna Nueva"),
        ("Creciente", "Creciente"),
        ("Cuarto Creciente", "Cuarto Creciente"),
        ("Gibosa Creciente", "Gibosa Creciente"),
        ("Luna Llena", "Luna Llena"),
        ("Gibosa Menguante", "Gibosa Menguante"),
        ("Cuarto Menguante", "Cuarto Menguante"),
        ("Menguante", "Menguante"),
    ]

    MAR_CHOICES = [
        ("TQ", "TQ"),  # Tranquila
        ("PO", "PO"),  # Poco Oleaje
        ("O", "O"),  # Oleaje
        ("MRJ", "MRJ"),  # Marejadas
        ("FMRJ", "FMRJ"),  # Fuertes Marejadas
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date = models.DateField(verbose_name="Fecha", unique=True, db_index=True)
    lp = models.CharField(max_length=20, choices=LUNA_CHOICES, verbose_name="Fase Lunar")
    nlp = models.CharField(max_length=20, choices=LUNA_CHOICES, verbose_name="Próxima Fase Lunar")
    nlpd = models.DateField(verbose_name="Fecha Próxima Fase")
    sunrise = models.TimeField(verbose_name="Salida Sol")
    sunset = models.TimeField(verbose_name="Puesta Sol")
    uv_index = models.IntegerField(verbose_name="Índice UV")

    class Meta:
        verbose_name = "Pronóstico"
        verbose_name_plural = "Pronósticos"
        ordering = ('-date',)
        default_permissions = ()
        permissions = (
            ("view_forecast", "Ver"),
            ("add_forecast", "Añadir"),
            ("change_forecast", "Editar"),
            ("delete_forecast", "Eliminar"),
        )

    def __str__(self):
        return f"Pronóstico detallado - {self.date.strftime('%d/%m/%Y')}"

    # ---- Bridge properties para modelos normalizados ----

    def get_region_data(self, region):
        """Retorna dict con los 3 períodos de una región."""
        periods = {}
        for p in self.regions.filter(region=region).order_by('period_order'):
            periods[p.period] = {
                'temp': p.temp,
                'weather': p.weather,
                'weather_icon': p.weather_icon,
                'wind_dir': p.wind_dir,
                'wind_speed': p.wind_speed,
                'sea': p.sea_note,
            }
        return periods

    def get_extended_days(self):
        """Retorna lista de días extendidos ordenados."""
        return self.extended_days.order_by('day_number').all()

    @property
    def north(self):
        return self.get_region_data('north')

    @property
    def interior(self):
        return self.get_region_data('interior')

    @property
    def south(self):
        return self.get_region_data('south')

    @property
    def extended_forecast(self):
        return self.get_extended_days()


class ForecastRegions(models.Model):
    REGION_CHOICES = [
        ('north', 'Costa Norte'),
        ('interior', 'Interior'),
        ('south', 'Costa Sur'),
    ]
    PERIOD_CHOICES = [
        ('morning', 'Mañana'),
        ('afternoon', 'Tarde'),
        ('night', 'Noche'),
    ]

    forecast = models.ForeignKey(
        Forecasts, on_delete=models.CASCADE, related_name='regions'
    )
    region = models.CharField(max_length=10, choices=REGION_CHOICES)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    period_order = models.IntegerField(default=0, editable=False)
    temp = models.IntegerField(verbose_name="Temperatura")
    weather = models.CharField(max_length=10, choices=Forecasts.TIEMPO_CHOICES, verbose_name="Tiempo")
    wind_dir = models.CharField(max_length=10, choices=Forecasts.VIENTO_DIRECCION_CHOICES, verbose_name="Dirección del Viento")
    wind_speed = models.CharField(max_length=5, verbose_name="Velocidad del Viento")
    sea_note = models.CharField(max_length=10, choices=Forecasts.MAR_CHOICES, blank=True, null=True, verbose_name="Mar")

    class Meta:
        verbose_name = "Pronóstico por Región"
        verbose_name_plural = "Pronósticos por Región"
        default_permissions = ()
        permissions = (
            ("view_forecastregions", "Ver"),
            ("add_forecastregions", "Añadir"),
            ("change_forecastregions", "Editar"),
            ("delete_forecastregions", "Eliminar"),
        )
        unique_together = ['forecast', 'region', 'period']
        ordering = ['forecast', 'region', 'period_order']

    def __str__(self):
        return f"{self.get_region_display()} - {self.get_period_display()}"

    def save(self, *args, **kwargs):
        period_order_map = {'morning': 1, 'afternoon': 2, 'night': 3}
        self.period_order = period_order_map.get(self.period, 0)
        super().save(*args, **kwargs)

    @property
    def weather_icon(self):
        from apps.common.utils import get_img_path
        return get_img_path(self.weather, self.period)


class ForecastExtendedDay(models.Model):
    forecast = models.ForeignKey(
        Forecasts, on_delete=models.CASCADE, related_name='extended_days'
    )
    day_number = models.IntegerField(verbose_name="Día")
    date = models.DateField(verbose_name="Fecha")
    min_temp = models.IntegerField(verbose_name="Temperatura Mínima")
    max_temp = models.IntegerField(verbose_name="Temperatura Máxima")
    weather = models.CharField(max_length=10, choices=Forecasts.TIEMPO_CHOICES, verbose_name="Tiempo")

    class Meta:
        verbose_name = "Día Extendido"
        verbose_name_plural = "Días Extendidos"
        default_permissions = ()
        permissions = (
            ("view_forecastextendedday", "Ver"),
            ("add_forecastextendedday", "Añadir"),
            ("change_forecastextendedday", "Editar"),
            ("delete_forecastextendedday", "Eliminar"),
        )
        unique_together = ['forecast', 'day_number']
        ordering = ['forecast', 'day_number']

    def clean(self):
        if self.min_temp is not None and self.max_temp is not None and self.min_temp >= self.max_temp:
            raise ValidationError('La temperatura mínima debe ser menor que la máxima.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Día {self.day_number} - {self.date}"

    @property
    def weather_icon(self):
        from apps.common.utils import get_img_path
        return get_img_path(self.weather, 'afternoon')


class BaseWarning(FileHandlerMixin, models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="%(class)s_warnings")
    summary = models.TextField(max_length=300, verbose_name="Resumen")
    file = models.FileField(upload_to=pdf_upload_path, verbose_name="Archivo PDF")
    valid_until = models.DateTimeField(verbose_name="Válido Hasta")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora de Creación")
    email_recipient_list = models.ForeignKey("EmailRecipientList", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Lista de Correos")

    file_fields = ['file']

    class Meta:
        abstract = True

    def __str__(self):
        return self.summary


class EarlyWarning(BaseWarning):
    class Meta:
        verbose_name = "Aviso de Alerta Temprana"
        verbose_name_plural = "Avisos de Alertas Tempranas"
        ordering = ['-date']
        default_permissions = ()
        permissions = (
            ("view_early_warning", "Ver"),
            ("add_early_warning", "Añadir"),
            ("change_early_warning", "Editar"),
            ("delete_early_warning", "Eliminar"),
        )


class TropicalCyclone(BaseWarning):
    class Meta:
        verbose_name = "Aviso de Ciclón Tropical"
        verbose_name_plural = "Avisos de Ciclones Tropicales"
        ordering = ['-date']
        default_permissions = ()
        permissions = (
            ("view_tropical_cyclone", "Ver"),
            ("add_tropical_cyclone", "Añadir"),
            ("change_tropical_cyclone", "Editar"),
            ("delete_tropical_cyclone", "Eliminar"),
        )


class StormWarning(BaseWarning):
    class Meta:
        verbose_name = "Aviso de Tormenta"
        verbose_name_plural = "Avisos de Tormentas"
        ordering = ['-date']
        default_permissions = ()
        permissions = (
            ("view_storm_warning", "Ver"),
            ("add_storm_warning", "Añadir"),
            ("change_storm_warning", "Editar"),
            ("delete_storm_warning", "Eliminar"),
        )


class Contract(SoftDeleteModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    subscription = models.OneToOneField(
        ServiceSubscription,
        on_delete=models.CASCADE,
        related_name='contract',
        verbose_name="Contrato"
    )
    number = models.CharField(max_length=50, verbose_name="Número de contrato")
    date = models.DateField(verbose_name="Fecha del contrato")
    commercial_registry = models.CharField(max_length=50, verbose_name="Registro Comercial")

    class Meta:
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"
        default_permissions = ()
        permissions = (
            ("view_contract", "Ver Contrato"),
            ("add_contract", "Añadir Contrato"),
            ("change_contract", "Editar Contrato"),
            ("delete_contract", "Eliminar Contrato"),
        )
        ordering = ('-date',)

    def __str__(self):
        return f"Contrato {self.number} - {self.subscription.customer.company_name}"


class Invoice(SoftDeleteModel, FileHandlerMixin):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    subscription = models.ForeignKey(
        ServiceSubscription,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='invoices',
        verbose_name="Suscripción"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='invoices',
        verbose_name="Cliente"
    )
    number = models.CharField(max_length=50, unique=True, verbose_name="Número de factura")
    issue_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de emisión")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto")
    pdf = models.FileField(upload_to='invoices/pdfs/', verbose_name="Archivo PDF", blank=True, null=True)
    is_cancelled = models.BooleanField(default=False, verbose_name="¿Anulada?")
    email_sent = models.BooleanField(default=False, verbose_name='Correo enviado')
    email_error = models.TextField(blank=True, null=True, verbose_name='Error al enviar')

    file_fields = ['pdf']

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ['-issue_date']
        default_permissions = ()
        permissions = (
            ("view_invoice", "Ver"),
            ("add_invoice", "Añadir"),
            ("change_invoice", "Editar"),
            ("delete_invoice", "Eliminar"),
        )

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError('El monto de la factura debe ser mayor que cero.')

    def __str__(self):
        if self.subscription:
            return f"Factura {self.number} - {self.subscription.customer.company_name}"
        return f"Factura {self.number} (manual)"


class InvoiceItem(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    subscription = models.ForeignKey(ServiceSubscription, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoice_items")
    codigo = models.CharField(max_length=50, blank=True)
    descripcion = models.TextField()
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    unidad_medida = models.CharField(max_length=5, default='U')
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    importe = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        if self.cantidad is not None and self.cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor que cero.')
        if self.precio is not None and self.precio <= 0:
            raise ValidationError('El precio debe ser mayor que cero.')

    def save(self, *args, **kwargs):
        self.importe = self.cantidad * self.precio
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Items"
        ordering = ['invoice', 'codigo']
        default_permissions = ()
        permissions = (
            ("view_invoice_item", "Ver"),
            ("add_invoice_item", "Añadir"),
            ("change_invoice_item", "Editar"),
            ("delete_invoice_item", "Eliminar"),
        )


class Certificate(SoftDeleteModel, FileHandlerMixin):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    subscription = models.ForeignKey(
        ServiceSubscription,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name="Suscripción"
    )
    issued_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de emisión")
    pdf = models.FileField(upload_to='certificates/pdfs/', verbose_name="Certificado PDF")

    file_fields = ['pdf']

    class Meta:
        verbose_name = "Certificado"
        verbose_name_plural = "Certificados"
        ordering = ['-issued_date']
        default_permissions = ()
        permissions = (
            ("view_certificate", "Ver"),
            ("add_certificate", "Añadir"),
            ("change_certificate", "Editar"),
            ("delete_certificate", "Eliminar"),
        )

    def __str__(self):
        return f"Certificado de {self.subscription.service.title} - {self.subscription.customer.company_name}"


class WeatherReport(FileHandlerMixin, models.Model):
    TYPE_CHOICES = [
        ('today', 'Hoy'),
        ('tomorrow', 'Mañana'),
        ('commentary', 'Comentario'),
        ('note', 'Nota'),
    ]
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Autor")
    date = models.DateTimeField(verbose_name="Fecha y Hora de Creación")
    summary = models.TextField(max_length=300, verbose_name="Resumen")
    content = models.TextField(blank=True, verbose_name="Contenido")
    file = models.FileField(upload_to=pdf_upload_path, verbose_name="Archivo PDF")
    email_recipient_list = models.ForeignKey("EmailRecipientList", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Lista de Correos")
    report_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Tipo")

    file_fields = ['file']

    def __str__(self):
        labels = dict(self.TYPE_CHOICES)
        return f"{labels.get(self.report_type, self.report_type)} - {self.date}"

    class Meta:
        verbose_name = "Reporte Meteorológico"
        verbose_name_plural = "Reportes Meteorológicos"
        ordering = ['-date']
        default_permissions = ()
        permissions = (
            ("view_weather_report", "Ver reportes meteorológicos"),
            ("view_weather_today", "Ver Tiempo Hoy"),
            ("add_weather_today", "Añadir Tiempo Hoy"),
            ("change_weather_today", "Editar Tiempo Hoy"),
            ("delete_weather_today", "Eliminar Tiempo Hoy"),
            ("view_weather_tomorrow", "Ver Tiempo Mañana"),
            ("add_weather_tomorrow", "Añadir Tiempo Mañana"),
            ("change_weather_tomorrow", "Editar Tiempo Mañana"),
            ("delete_weather_tomorrow", "Eliminar Tiempo Mañana"),
            ("view_weather_commentary", "Ver Comentario del Tiempo"),
            ("add_weather_commentary", "Añadir Comentario del Tiempo"),
            ("change_weather_commentary", "Editar Comentario del Tiempo"),
            ("delete_weather_commentary", "Eliminar Comentario del Tiempo"),
            ("view_weather_note", "Ver Nota Meteorológica"),
            ("add_weather_note", "Añadir Nota Meteorológica"),
            ("change_weather_note", "Editar Nota Meteorológica"),
            ("delete_weather_note", "Eliminar Nota Meteorológica"),
        )


class EmailRecipientList(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Lista")
    description = models.TextField(blank=True, verbose_name="Descripción")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Lista de Correo"
        verbose_name_plural = "Listas de Correo"
        ordering = ('name',)
        default_permissions = ()
        permissions = (
            ("view_email_recipient_list", "Ver"),
            ("add_email_recipient_list", "Añadir"),
            ("change_email_recipient_list", "Editar"),
            ("delete_email_recipient_list", "Eliminar"),
        )


class EmailRecipient(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True, verbose_name="Correo Electrónico")
    recipient_list = models.ForeignKey(EmailRecipientList, on_delete=models.CASCADE, related_name="recipients", verbose_name="Lista de Correo")

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Destinatario de Correo"
        verbose_name_plural = "Destinatarios de Correo"
        ordering = ('email',)
        default_permissions = ()
        permissions = (
            ("view_email_recipient", "Ver"),
            ("add_email_recipient", "Añadir"),
            ("change_email_recipient", "Editar"),
            ("delete_email_recipient", "Eliminar"),
        )
