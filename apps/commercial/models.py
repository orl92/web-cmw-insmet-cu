import uuid
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Count, Q
from django.utils import timezone

from apps.core.models import FileHandlerMixin, SoftDeleteModel, image_upload_path, pdf_upload_path
from apps.core.validators import (
    validate_account,
    validate_image_upload,
    validate_nit,
    validate_phones,
    validate_reeup,
)


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
        upload_to=image_upload_path,
        blank=True,
        null=True,
        verbose_name='Imagen',
        validators=[validate_image_upload],
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
        """Estado único del ciclo de vida, para listados y exportaciones.

        `cancelada` sale de la baja lógica (`record_active`), no de un valor
        propio de `payment_status`: anular ya marca `record_active=False`, y
        llevar el mismo dato en dos campos es la forma más directa de que
        diverjan. Tampoco se mira `end_date`: una suscripción pagada que venció
        estuvo pagada, y el periodo es un dato aparte, no un estado de pago.
        """
        if not self.record_active:
            return 'cancelada'
        return {
            'requested': 'solicitado',
            'pending': 'pendiente',
            'paid': 'pagado',
        }.get(self.payment_status, 'solicitado')

    def __str__(self):
        return f'{self.customer.company_name} - {self.service.title}'


class InvoiceQuerySet(models.QuerySet):
    def for_subscription(self, sub):
        """Facturas de una suscripción, por cualquiera de los dos caminos.

        `Invoice.subscription` es un ancla de conveniencia y queda NULL cuando la
        factura cubre varias suscripciones: la facturación por lote agrupa
        suscripciones con el mismo período y la manual de varios servicios sólo
        cuelga la primera. El vínculo que nunca falta es el de cada línea
        (`InvoiceItem.subscription`), así que leer sólo la relación inversa deja
        al cliente sin botones de factura justo en esos casos.
        """
        return self.filter(Q(subscription=sub) | Q(items__subscription=sub)).distinct()

    def with_display_status(self):
        """Anota el conteo de líneas pagadas para no repetir la consulta por fila.

        `Invoice.status_display` cae a las líneas cuando no encuentra estas
        anotaciones, así que sin esto el listado pagaría una consulta por
        factura.
        """
        return self.annotate(
            items_total=Count(
                'items__subscription',
                distinct=True,
                filter=Q(items__subscription__isnull=False),
            ),
            items_paid=Count(
                'items__subscription',
                distinct=True,
                filter=Q(items__subscription__payment_status='paid'),
            ),
        )


class Invoice(SoftDeleteModel, FileHandlerMixin):
    objects = InvoiceQuerySet.as_manager()
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

    class PdfStatus(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        READY = 'ready', 'Generado'
        FAILED = 'failed', 'Falló'

    class EmailStatus(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        SENT = 'sent', 'Enviado'
        FAILED = 'failed', 'Falló'

    pdf_status = models.CharField(
        max_length=10,
        choices=PdfStatus.choices,
        default=PdfStatus.PENDING,
        verbose_name='Estado del PDF',
    )
    pdf_error = models.TextField(blank=True, null=True, verbose_name='Error al generar el PDF')
    email_status = models.CharField(
        max_length=10,
        choices=EmailStatus.choices,
        default=EmailStatus.PENDING,
        verbose_name='Estado del correo',
    )
    email_error = models.TextField(blank=True, null=True, verbose_name='Error al enviar')

    file_fields = ['pdf']

    @property
    def pdf_ready(self):
        """El PDF se puede mostrar y descargar solo si el render terminó bien.

        No alcanza con que el archivo exista: un render fallido a mitad de
        camino deja el campo `pdf` PopulationError. El estado explícito es lo
        que decide si los botones aparecen.
        """
        return self.pdf_status == self.PdfStatus.READY and bool(self.pdf)

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

    @property
    def status_display(self):
        """Estado derivado: la fuente de verdad del pago es la suscripción.

        No hay campo de estado en la factura a propósito. La facturación por
        lote cubre varias suscripciones y cada una se aprueba por separado, así
        que un campo propio sólo añadiría una segunda fuente de verdad capaz de
        divergir de la real. Se lee de las líneas, o de las anotaciones que
        deja `with_display_status()` cuando el listado ya las trajo.
        """
        if self.is_cancelled:
            return 'cancelada'
        if hasattr(self, 'items_total'):
            total, paid = self.items_total, self.items_paid
        else:
            # `filter`, nunca `exclude`: `items` es una relación inversa, y
            # excluir sobre una relación multi-valorada arma un subquery que
            # termina descartando todas las líneas.
            subs = self.items.filter(subscription__isnull=False).values_list(
                'subscription__payment_status', flat=True
            )
            states = list(subs)
            total, paid = len(states), states.count('paid')
        return 'pagada' if total and paid == total else 'pendiente'

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
