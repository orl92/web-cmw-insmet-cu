import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from apps.common.utils import FileHandlerMixin, SoftDeleteModel


class Customer(SoftDeleteModel):
    class ClientType(models.TextChoices):
        NATURAL = 'natural', 'Persona Natural'
        JURIDICA = 'juridica', 'Persona Jurídica'

    reeup_validator = RegexValidator(
        regex=r'^\d{3}\.\d{1,2}\.\d{4,5}$',
        message='El REEUP debe tener el formato ###.#.####, ###.#.#####, ###.##.#### o ###.##.#####'
    )
    nit_validator = RegexValidator(
        regex=r'^\d{11}$',
        message='El NIT debe estar compuesto por 11 dígitos numéricos.'
    )
    account_validator = RegexValidator(
        regex=r'^\d{16}$',
        message='La cuenta bancaria debe tener 16 dígitos numéricos.'
    )
    phone_validator = RegexValidator(
        regex=r'^\d{8}$',
        message='El número de teléfono debe tener 8 dígitos (sin espacios ni guiones).'
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    client_type = models.CharField(
        max_length=8,
        choices=ClientType.choices,
        default=ClientType.JURIDICA,
        verbose_name="Tipo de Cliente"
    )
    company_name = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Nombre de la Empresa"
    )
    reeup = models.CharField(
        max_length=12, validators=[reeup_validator], blank=True, null=True, verbose_name="REEUP"
    )
    nit = models.CharField(
        max_length=11, validators=[nit_validator], blank=True, null=True, verbose_name="NIT"
    )
    account = models.CharField(max_length=16, validators=[account_validator], verbose_name="Cuenta Bancaria")
    agency_bank = models.CharField(max_length=100, blank=True, null=True, verbose_name="Agencia Bancaria")
    address = models.TextField(verbose_name="Dirección")
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Usuario")
    phone = models.CharField(max_length=8, validators=[phone_validator], verbose_name="Número de Teléfono")
    accept_terms = models.BooleanField(default=False, verbose_name="Aceptó Términos")

    def __str__(self):
        if self.client_type == self.ClientType.NATURAL:
            return f"{self.user.get_full_name() or self.user.username}"
        return self.company_name or self.user.get_full_name() or self.user.username

    class Meta:
        managed = False
        db_table = 'dashboard_customer'
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        default_permissions = ()
        permissions = (
            ("view_customer", "Ver"),
            ("add_customer", "Añadir"),
            ("change_customer", "Editar"),
            ("delete_customer", "Eliminar"),
        )


class Service(SoftDeleteModel, FileHandlerMixin, models.Model):
    PUBLIC = 'public'
    COMMERCIAL = 'commercial'
    TYPE_CHOICES = [
        (PUBLIC, 'Público'),
        (COMMERCIAL, 'Comercial'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Usuario', related_name='created_services')
    title = models.CharField(max_length=100, verbose_name='Título')
    summary = models.CharField(max_length=500, verbose_name='Resumen')
    service_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=PUBLIC, verbose_name='Tipo de Servicio')
    pdf = models.FileField(upload_to='services/pdfs/', blank=True, null=True, verbose_name='Archivo PDF')
    image = models.ImageField(upload_to='services/images/', blank=True, null=True, verbose_name='Imagen')
    code = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="Código del servicio")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio (CUP)", help_text="Precio unitario del servicio")

    file_fields = ['pdf', 'image']

    def __str__(self):
        return self.title

    def get_image_url(self):
        if self.image:
            return self.image.url
        return f'{settings.STATIC_URL}dist/img/default.svg'

    class Meta:
        managed = False
        db_table = 'dashboard_service'
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        default_permissions = ()
        permissions = (
            ('view_service', 'Ver'),
            ('add_service', 'Añadir'),
            ('change_service', 'Editar'),
            ('delete_service', 'Eliminar'),
        )


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
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Cliente")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Servicio")
    start_date = models.DateTimeField(verbose_name="Fecha de inicio", null=True, blank=True)
    end_date = models.DateTimeField(verbose_name="Fecha de expiración", null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='requested', verbose_name="Estado de pago")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name="Método de pago", blank=True, null=True)

    file_fields = []

    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError('La fecha de inicio debe ser anterior a la fecha de expiración.')

    @property
    def is_active(self):
        return self.payment_status == 'paid' and self.end_date and self.end_date > timezone.now()

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

    class Meta:
        managed = False
        db_table = 'dashboard_servicesubscription'
        verbose_name = "Suscripción de servicio"
        verbose_name_plural = "Suscripciones de servicios"
        default_permissions = ()
        permissions = (
            ("view_subscription", "Ver"),
            ("add_subscription", "Añadir"),
            ("change_subscription", "Editar"),
            ("delete_subscription", "Eliminar"),
        )

    def __str__(self):
        return f"{self.customer.company_name} - {self.service.title}"
