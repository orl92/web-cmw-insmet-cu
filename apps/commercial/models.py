import uuid
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import FileHandlerMixin, SoftDeleteModel, image_upload_path, pdf_upload_path
from apps.core.validators import validate_account, validate_nit, validate_phones, validate_reeup


class Customer(SoftDeleteModel):
    class ClientType(models.TextChoices):
        NATURAL = 'natural', 'Persona Natural'
        JURIDICA = 'juridica', 'Persona Jurídica'

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    client_type = models.CharField(
        max_length=8,
        choices=ClientType.choices,
        default=ClientType.JURIDICA,
        verbose_name='Tipo de Cliente',
    )
    identity_document = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Documento de identidad',
    )
    company_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Nombre de la Empresa',
    )
    reeup = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        unique=True,
        verbose_name='REEUP',
        validators=[validate_reeup],
    )
    nit = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        unique=True,
        verbose_name='NIT',
        validators=[validate_nit],
    )
    account = models.CharField(
        max_length=16,
        unique=True,
        verbose_name='Cuenta Bancaria',
        validators=[validate_account],
    )
    agency_bank = models.CharField(
        max_length=100, blank=True, null=True, verbose_name='Agencia Bancaria'
    )
    address = models.TextField(verbose_name='Dirección')
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Usuario',
        related_name='commercial_customer',
    )
    phone = models.CharField(
        max_length=100,
        verbose_name='Teléfonos',
        validators=[validate_phones],
    )
    accept_terms = models.BooleanField(default=False, verbose_name='Aceptó Términos')

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        default_permissions = ()
        permissions = (
            ('view_customer', 'Ver'),
            ('add_customer', 'Añadir'),
            ('change_customer', 'Editar'),
            ('delete_customer', 'Eliminar'),
        )

    def __str__(self):
        if self.client_type == self.ClientType.NATURAL:
            return f'{self.user.get_full_name() or self.user.username}'
        return self.company_name or self.user.get_full_name() or self.user.username


class Service(SoftDeleteModel, FileHandlerMixin, models.Model):
    PUBLIC = 'public'
    COMMERCIAL = 'commercial'
    TYPE_CHOICES = [
        (PUBLIC, 'Público'),
        (COMMERCIAL, 'Comercial'),
    ]

    PERIOD_DAYS = 1
    PERIOD_MONTHS = 1

    SERVICE_CATEGORY_CHOICES = [
        ('agrometeo', 'Agrometeorológico'),
        ('pronostico', 'Pronóstico'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Usuario',
        related_name='commercial_created_services',
    )
    title = models.CharField(max_length=100, verbose_name='Título')
    summary = models.CharField(max_length=500, verbose_name='Resumen')
    service_type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default=PUBLIC, verbose_name='Tipo de Servicio'
    )
    pdf = models.FileField(
        upload_to=pdf_upload_path, blank=True, null=True, verbose_name='Archivo PDF'
    )
    image = models.ImageField(
        upload_to=image_upload_path, blank=True, null=True, verbose_name='Imagen'
    )
    code = models.CharField(
        max_length=50, unique=True, null=True, blank=True, verbose_name='Código del servicio'
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Precio (CUP)'
    )
    service_category = models.CharField(
        max_length=10,
        choices=SERVICE_CATEGORY_CHOICES,
        default='pronostico',
        verbose_name='Categoría del servicio',
    )

    file_fields = ['pdf', 'image']

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        default_permissions = ()
        permissions = (
            ('view_service', 'Ver'),
            ('add_service', 'Añadir'),
            ('change_service', 'Editar'),
            ('delete_service', 'Eliminar'),
        )

    def __str__(self):
        return self.title

    def get_image_url(self):
        if self.image:
            return self.image.url
        return f'{settings.STATIC_URL}dist/img/default.svg'

    def get_billing_period_display(self):
        return 'mes' if self.service_category == 'agrometeo' else 'día'

    def get_price_per_period_display(self):
        if self.price is None:
            return ''
        return f'${self.price:.2f} / {self.get_billing_period_display()}'

    @staticmethod
    def compute_end_date(start_date, quantity, category='pronostico'):
        if category == 'agrometeo':
            return start_date + relativedelta(months=quantity)
        return start_date + timedelta(days=quantity)


class ServiceSubscription(SoftDeleteModel, FileHandlerMixin, models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('requested', 'Solicitado'),
        ('pending', 'Pendiente de pago'),
        ('paid', 'Pagado'),
        ('expired', 'Expirado'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('qr', 'Pago por Código QR'),
        ('transfer', 'Transferencia Bancaria'),
        ('presencial', 'Pago Presencial'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='Cliente')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name='Servicio')
    start_date = models.DateTimeField(verbose_name='Fecha de inicio', null=True, blank=True)
    end_date = models.DateTimeField(verbose_name='Fecha de expiración', null=True, blank=True)
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad',
        help_text='Meses (agrometeo) o días (pronóstico)',
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='requested',
        verbose_name='Estado de pago',
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name='Método de pago',
        blank=True,
        null=True,
    )

    file_fields = []

    class Meta:
        verbose_name = 'Suscripción de servicio'
        verbose_name_plural = 'Suscripciones de servicios'
        default_permissions = ()
        permissions = (
            ('view_subscription', 'Ver'),
            ('add_subscription', 'Añadir'),
            ('change_subscription', 'Editar'),
            ('delete_subscription', 'Eliminar'),
        )

    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError('La fecha de inicio debe ser anterior a la fecha de expiración.')

    @property
    def is_active(self):
        return self.payment_status == 'paid' and self.end_date and self.end_date > timezone.now()

    def get_quantity_period_display(self):
        """Cantidad + unidad de facturación: `1 día`, `3 meses`, `30 días`."""
        unit = self.service.get_billing_period_display()  # 'día' | 'mes'
        plural = {'día': 'días', 'mes': 'meses'}.get(unit, f'{unit}s')
        return f'{self.quantity} {plural if self.quantity != 1 else unit}'

    @property
    def status_display(self):
        if self.payment_status == 'paid' and self.end_date and self.end_date > timezone.now():
            return 'activo'
        elif self.payment_status == 'pending':
            return 'pendiente de pago'
        elif self.payment_status == 'requested':
            return 'solicitado'
        else:
            return 'expirado'

    def __str__(self):
        return f'{self.customer.company_name} - {self.service.title}'


class Invoice(SoftDeleteModel, FileHandlerMixin):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    subscription = models.ForeignKey(
        ServiceSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name='Suscripción',
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name='Cliente',
    )
    number = models.CharField(max_length=50, unique=True, verbose_name='Número de factura')
    issue_date = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de emisión')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto')
    pdf = models.FileField(
        upload_to=pdf_upload_path, verbose_name='Archivo PDF', blank=True, null=True
    )
    is_cancelled = models.BooleanField(default=False, verbose_name='¿Anulada?')
    email_sent = models.BooleanField(default=False, verbose_name='Correo enviado')
    email_error = models.TextField(blank=True, null=True, verbose_name='Error al enviar')

    file_fields = ['pdf']

    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-issue_date']
        default_permissions = ()
        permissions = (
            ('view_invoice', 'Ver'),
            ('add_invoice', 'Añadir'),
            ('change_invoice', 'Editar'),
            ('delete_invoice', 'Eliminar'),
        )

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError('El monto de la factura debe ser mayor que cero.')

    def __str__(self):
        if self.subscription:
            return f'Factura {self.number} - {self.subscription.customer.company_name}'
        return f'Factura {self.number} (manual)'


class InvoiceItem(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    subscription = models.ForeignKey(
        ServiceSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_items',
    )
    codigo = models.CharField(max_length=50, blank=True)
    descripcion = models.TextField()
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    unidad_medida = models.CharField(max_length=5, default='U')
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    importe = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
        ordering = ['invoice', 'codigo']
        default_permissions = ()
        permissions = (
            ('view_invoice_item', 'Ver'),
            ('add_invoice_item', 'Añadir'),
            ('change_invoice_item', 'Editar'),
            ('delete_invoice_item', 'Eliminar'),
        )

    def clean(self):
        if self.cantidad is not None and self.cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor que cero.')
        if self.precio is not None and self.precio <= 0:
            raise ValidationError('El precio debe ser mayor que cero.')

    def save(self, *args, **kwargs):
        self.importe = self.cantidad * self.precio
        self.full_clean()
        super().save(*args, **kwargs)


class Contract(SoftDeleteModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    subscription = models.OneToOneField(
        ServiceSubscription,
        on_delete=models.CASCADE,
        related_name='contract',
        verbose_name='Contrato',
    )
    number = models.CharField(max_length=50, verbose_name='Número de contrato')
    date = models.DateField(verbose_name='Fecha del contrato')
    commercial_registry = models.CharField(max_length=50, verbose_name='Registro Comercial')

    class Meta:
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'
        default_permissions = ()
        permissions = (
            ('view_contract', 'Ver'),
            ('add_contract', 'Añadir'),
            ('change_contract', 'Editar'),
            ('delete_contract', 'Eliminar'),
        )
        ordering = ('-date',)

    def __str__(self):
        return f'Contrato {self.number} - {self.subscription.customer.company_name}'


class Certificate(SoftDeleteModel, FileHandlerMixin):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    subscription = models.ForeignKey(
        ServiceSubscription,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name='Suscripción',
    )
    issued_date = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de emisión')
    pdf = models.FileField(upload_to=pdf_upload_path, verbose_name='Certificado PDF')

    file_fields = ['pdf']

    class Meta:
        verbose_name = 'Certificado'
        verbose_name_plural = 'Certificados'
        ordering = ['-issued_date']
        default_permissions = ()
        permissions = (
            ('view_certificate', 'Ver'),
            ('add_certificate', 'Añadir'),
            ('change_certificate', 'Editar'),
            ('delete_certificate', 'Eliminar'),
        )

    def __str__(self):
        service = self.subscription.service
        customer = self.subscription.customer
        return f'Certificado de {service.title} - {customer.company_name}'
