import os
import re
import uuid

from django.db import models
from django.utils import timezone

from apps.core.validators import validate_account, validate_nit, validate_phones, validate_reeup


def pdf_upload_path(instance, filename):
    cls_name = instance.__class__.__name__.lower()
    uid = str(instance.uuid)
    safe_name = re.sub(r'[^\w\.\-]', '_', filename)
    return f'pdf/{cls_name}/{uid}_{safe_name}'


def image_upload_path(instance, filename):
    cls_name = instance.__class__.__name__.lower()
    uid = str(instance.uuid)
    safe_name = re.sub(r'[^\w\.\-]', '_', filename)
    return f'img/{cls_name}/{uid}_{safe_name}'


class FileHandlerMixin(models.Model):
    file_fields = []

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk:
            for field_name in self.file_fields:
                old_instance = self.__class__.objects.filter(pk=self.pk).first()
                if old_instance:
                    old_file = getattr(old_instance, field_name)
                    new_file = getattr(self, field_name)
                    if old_file and old_file != new_file and os.path.isfile(old_file.path):
                        os.remove(old_file.path)
        super().save(*args, **kwargs)

    def _cleanup_files(self):
        for field_name in self.file_fields:
            file_field = getattr(self, field_name)
            if file_field and os.path.isfile(file_field.path):
                os.remove(file_field.path)

    def delete(self, *args, **kwargs):
        self._cleanup_files()
        super().delete(*args, **kwargs)


class SoftDeleteModel(models.Model):
    record_active = models.BooleanField(default=True, verbose_name='Registro activo')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Eliminado en')

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        if hasattr(self, '_cleanup_files'):
            self._cleanup_files()
        self.record_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['record_active', 'deleted_at'])

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)


TIEMPO_CHOICES = [
    ('despejado', 'Despejado'),
    ('mayormente_despejado', 'Mayormente despejado'),
    ('parcialmente_nublado', 'Parcialmente nublado'),
    ('mayormente_nublado', 'Mayormente nublado'),
    ('nublado', 'Nublado'),
    ('lluvias', 'Lluvias'),
    ('lluvias_debiles', 'Lluvias débiles'),
    ('chubascos', 'Chubascos'),
    ('chubascos_electricos', 'Chubascos eléctricos'),
    ('chubascos_lluvias', 'Chubascos y lluvias'),
    ('tormenta', 'Tormenta eléctrica'),
]

VIENTO_DIRECCION_CHOICES = [
    ('N', 'Norte'),
    ('NNE', 'Norte-Noreste'),
    ('NE', 'Noreste'),
    ('ENE', 'Este-Noreste'),
    ('E', 'Este'),
    ('ESE', 'Este-Sureste'),
    ('SE', 'Sureste'),
    ('SSE', 'Sur-Sureste'),
    ('S', 'Sur'),
    ('SSO', 'Sur-Suroeste'),
    ('SO', 'Suroeste'),
    ('OSO', 'Oeste-Suroeste'),
    ('O', 'Oeste'),
    ('ONO', 'Oeste-Noroeste'),
    ('NO', 'Noroeste'),
    ('NNO', 'Norte-Noroeste'),
    ('variable', 'Variable'),
    ('calmado', 'Calmado'),
]

LUNA_CHOICES = [
    ('nueva', 'Luna nueva'),
    ('creciente', 'Luna creciente'),
    ('cuarto_creciente', 'Cuarto creciente'),
    ('creciente_gibosa', 'Creciente gibosa'),
    ('llena', 'Luna llena'),
    ('menguante_gibosa', 'Menguante gibosa'),
    ('cuarto_menguante', 'Cuarto menguante'),
    ('menguante', 'Luna menguante'),
]

MAR_CHOICES = [
    ('0', '0 — Calma'),
    ('1', '1 — Rizada'),
    ('2', '2 — Marejadilla'),
    ('3', '3 — Marejada'),
    ('4', '4 — Fuerte marejada'),
    ('5', '5 — Gruesa'),
    ('6', '6 — Muy gruesa'),
    ('7', '7 — Montaña'),
    ('8', '8 — Montañosa'),
    ('9', '9 — Excepcional'),
]


class SiteConfiguration(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    maintenance_mode = models.BooleanField(default=True, verbose_name='Modo mantenimiento')

    class Meta:
        verbose_name = 'Configuración del sitio'
        verbose_name_plural = 'Configuración del sitio'
        default_permissions = ()
        permissions = [
            ('view_siteconfiguration', 'Ver'),
            ('change_siteconfiguration', 'Editar'),
        ]

    def __str__(self):
        return 'Configuración del sitio'

    def save(self, *args, **kwargs):
        if not self.pk and SiteConfiguration.objects.exists():
            return
        super().save(*args, **kwargs)


class CompanySettings(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=255, verbose_name='Nombre de la empresa')
    direccion = models.TextField(verbose_name='Dirección')
    codigo_reeup = models.CharField(
        max_length=50, verbose_name='Código REEUP', validators=[validate_reeup]
    )
    nit = models.CharField(max_length=50, verbose_name='NIT', validators=[validate_nit])
    cuenta_bancaria = models.CharField(
        max_length=50, verbose_name='Cuenta bancaria', validators=[validate_account]
    )
    agencia_bancaria = models.CharField(max_length=100, verbose_name='Agencia bancaria')
    telefonos = models.CharField(
        max_length=100, verbose_name='Teléfonos', validators=[validate_phones]
    )
    registro_comercial = models.CharField(
        max_length=50,
        verbose_name='Registro Comercial',
        help_text='Ej: A09404',
    )

    class Meta:
        verbose_name = 'Datos de la empresa'
        verbose_name_plural = 'Datos de la empresa'
        default_permissions = ()
        permissions = [
            ('view_companysettings', 'Ver'),
            ('change_companysettings', 'Editar'),
        ]

    def __str__(self):
        return self.nombre

    @classmethod
    def get_instance(cls):
        instance = cls.objects.first()
        if not instance:
            instance = cls.objects.create(
                nombre='Centro Meteorológico Provincial Camagüey',
                direccion='Calle 1ra #120 entre 2da y 3ra, Reparto La Vigía, Camagüey, Cuba',
                codigo_reeup='',
                nit='',
                cuenta_bancaria='',
                agencia_bancaria='',
                telefonos='',
                registro_comercial='',
            )
        return instance


class EmailRecipientList(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')

    class Meta:
        verbose_name = 'Lista de correo'
        verbose_name_plural = 'Listas de correo'
        default_permissions = ()
        permissions = [
            ('view_emailrecipientlist', 'Ver'),
            ('add_emailrecipientlist', 'Añadir'),
            ('change_emailrecipientlist', 'Editar'),
            ('delete_emailrecipientlist', 'Eliminar'),
        ]

    def __str__(self):
        return self.name


class EmailRecipient(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, verbose_name='Correo electrónico')
    recipient_list = models.ForeignKey(
        EmailRecipientList,
        on_delete=models.CASCADE,
        related_name='recipients',
        verbose_name='Lista de correo',
    )

    class Meta:
        verbose_name = 'Correo'
        verbose_name_plural = 'Correos'
        default_permissions = ()
        permissions = [
            ('view_emailrecipient', 'Ver'),
            ('add_emailrecipient', 'Añadir'),
            ('change_emailrecipient', 'Editar'),
            ('delete_emailrecipient', 'Eliminar'),
        ]

    def __str__(self):
        return self.email
