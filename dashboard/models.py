import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

from common.utils import PDFModel

# Create your models here.


class SiteConfiguration(models.Model):
    id = models.AutoField(primary_key=True)  # ID predeterminado de Django
    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True
    )  # Identificador único adicional
    maintenance_mode = models.BooleanField(
        default=True
    )  # Modo de mantenimiento activado por defecto

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

    def __str__(self):
        return f"Modo Mantenimiento: {'Activado' if self.maintenance_mode else 'Desactivado'}"


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


class Province(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=15, verbose_name="Nombre")
    code = models.CharField(max_length=5, unique=True, verbose_name="Código")

    class Meta:
        verbose_name = "Provincia"
        verbose_name_plural = "Provincias"
        default_permissions = ()
        permissions = (
            ("view_province", "Ver"),
            ("add_province", "Añadir"),
            ("change_province", "Editar"),
            ("delete_province", "Eliminar"),
        )

    def __str__(self):
        return self.name


class Town(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    province = models.ForeignKey(
        Province,
        on_delete=models.SET_NULL,
        null=True,
        related_name="towns",
        verbose_name="Provincia",
    )
    name = models.CharField(max_length=25, verbose_name="Nombre")
    latitude = models.FloatField(verbose_name="Latitud")
    longitude = models.FloatField(verbose_name="Longitud")

    class Meta:
        verbose_name = "Municipio"
        verbose_name_plural = "Municipios"
        default_permissions = ()
        permissions = (
            ("view_town", "Ver"),
            ("add_town", "Añadir"),
            ("change_town", "Editar"),
            ("delete_town", "Eliminar"),
        )

    def __str__(self):
        return self.name


class Station(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    province = models.ForeignKey(
        Province,
        on_delete=models.SET_NULL,
        null=True,
        related_name="stations",
        verbose_name="Provincia",
    )
    name = models.CharField(max_length=15, verbose_name="Nombre")
    number = models.IntegerField(unique=True, verbose_name="Número")
    latitude = models.FloatField(verbose_name="Latitud")
    longitude = models.FloatField(verbose_name="Longitud")

    class Meta:
        verbose_name = "Estación"
        verbose_name_plural = "Estaciones"
        default_permissions = ()
        permissions = (
            ("view_station", "Ver"),
            ("add_station", "Añadir"),
            ("change_station", "Editar"),
            ("delete_station", "Eliminar"),
        )

    def __str__(self):
        return self.name


class Forecasts(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date = models.DateField(verbose_name="Fecha", unique=True, db_index=True)
    ntm = models.IntegerField(verbose_name="Temperatura Mañana")
    nta = models.IntegerField(verbose_name="Temperatura Tarde (Max)")
    ntn = models.IntegerField(verbose_name="Temperatura Noche")
    nwm = models.CharField(
        max_length=10, choices=TIEMPO_CHOICES, verbose_name="Tiempo Mañana"
    )
    nwa = models.CharField(
        max_length=10, choices=TIEMPO_CHOICES, verbose_name="Tiempo Tarde"
    )
    nwn = models.CharField(
        max_length=10, choices=TIEMPO_CHOICES, verbose_name="Tiempo Noche"
    )
    nwddm = models.CharField(
        max_length=10,
        choices=VIENTO_DIRECCION_CHOICES,
        verbose_name="Dirección del Viento Mañana",
    )
    nwdda = models.CharField(
        max_length=10,
        choices=VIENTO_DIRECCION_CHOICES,
        verbose_name="Dirección del Viento Tarde",
    )
    nwddn = models.CharField(
        max_length=10,
        choices=VIENTO_DIRECCION_CHOICES,
        verbose_name="Dirección del Viento Noche",
    )
    nwdfm = models.CharField(max_length=5, verbose_name="Velocidad del Viento Mañana")
    nwdfa = models.CharField(max_length=5, verbose_name="Velocidad del Viento Tarde")
    nwdfn = models.CharField(max_length=5, verbose_name="Velocidad del Viento Noche")
    nsm = models.CharField(
        max_length=10, choices=MAR_CHOICES, verbose_name="Mar Mañana"
    )
    nsa = models.CharField(max_length=10, choices=MAR_CHOICES, verbose_name="Mar Tarde")
    nsn = models.CharField(max_length=10, choices=MAR_CHOICES, verbose_name="Mar Noche")
    itm = models.IntegerField(verbose_name="Temperatura Mañana")
    ita = models.IntegerField(verbose_name="Temperatura Tarde (Max)")
    itn = models.IntegerField(verbose_name="Temperatura Noche")
    iwm = models.CharField(
        max_length=10, choices=TIEMPO_CHOICES, verbose_name="Tiempo Mañana"
    )
    iwa = models.CharField(
        max_length=10, choices=TIEMPO_CHOICES, verbose_name="Tiempo Tarde"
    )
    iwn = models.CharField(
        max_length=10, choices=TIEMPO_CHOICES, verbose_name="Tiempo Noche"
    )
    iwddm = models.CharField(
        max_length=10,
        choices=VIENTO_DIRECCION_CHOICES,
        verbose_name="Dirección del Viento Mañana",
    )
    iwdda = models.CharField(
        max_length=10,
        choices=VIENTO_DIRECCION_CHOICES,
        verbose_name="Dirección del Viento Tarde",
    )
    iwddn = models.CharField(
        max_length=10,
        choices=VIENTO_DIRECCION_CHOICES,
        verbose_name="Dirección del Viento Noche",
    )
    iwdfm = models.CharField(max_length=5, verbose_name="Velocidad del Viento Mañana")
    iwdfa = models.CharField(max_length=5, verbose_name="Velocidad del Viento Tarde")
    iwdfn = models.CharField(max_length=5, verbose_name="Velocidad del Viento Noche")
    stm = models.IntegerField(verbose_name="Temperatura Mañana")
    sta = models.IntegerField(verbose_name="Temperatura Tarde (Max)")
    stn = models.IntegerField(verbose_name="Temperatura Noche")
    swm = models.CharField(
        max_length=10, choices=TIEMPO_CHOICES, verbose_name="Tiempo Mañana"
    )
    swa = models.CharField(
        max_length=10, choices=TIEMPO_CHOICES, verbose_name="Tiempo Tarde"
    )
    swn = models.CharField(
        max_length=10, choices=TIEMPO_CHOICES, verbose_name="Tiempo Noche"
    )
    swddm = models.CharField(
        max_length=10,
        choices=VIENTO_DIRECCION_CHOICES,
        verbose_name="Dirección del Viento Mañana",
    )
    swdda = models.CharField(
        max_length=10,
        choices=VIENTO_DIRECCION_CHOICES,
        verbose_name="Dirección del Viento Tarde",
    )
    swddn = models.CharField(
        max_length=10,
        choices=VIENTO_DIRECCION_CHOICES,
        verbose_name="Dirección del Viento Noche",
    )
    swdfm = models.CharField(max_length=5, verbose_name="Velocidad del Viento Mañana")
    swdfa = models.CharField(max_length=5, verbose_name="Velocidad del Viento Tarde")
    swdfn = models.CharField(max_length=5, verbose_name="Velocidad del Viento Noche")
    ssm = models.CharField(
        max_length=10, choices=MAR_CHOICES, verbose_name="Mar Mañana"
    )
    ssa = models.CharField(max_length=10, choices=MAR_CHOICES, verbose_name="Mar Tarde")
    ssn = models.CharField(max_length=10, choices=MAR_CHOICES, verbose_name="Mar Noche")
    day1_date = models.DateField(verbose_name="Fecha")
    day1_min_temp = models.IntegerField(verbose_name="Temperatura Mínima")
    day1_max_temp = models.IntegerField(verbose_name="Temperatura Máxima")
    day1_weather = models.CharField(
        max_length=10, choices=TIEMPO_CHOICES, verbose_name="Tiempo"
    )
    day2_date = models.DateField(verbose_name="Fecha")
    day2_min_temp = models.IntegerField(verbose_name="Temperatura Mínima")
    day2_max_temp = models.IntegerField(verbose_name="Temperatura Máxima")
    day2_weather = models.CharField(
        max_length=10, choices=TIEMPO_CHOICES, verbose_name="Tiempo"
    )
    day3_date = models.DateField(verbose_name="Fecha")
    day3_min_temp = models.IntegerField(verbose_name="Temperatura Mínima")
    day3_max_temp = models.IntegerField(verbose_name="Temperatura Máxima")
    day3_weather = models.CharField(
        max_length=10, choices=TIEMPO_CHOICES, verbose_name="Tiempo"
    )
    day4_date = models.DateField(verbose_name="Fecha")
    day4_min_temp = models.IntegerField(verbose_name="Temperatura Mínima")
    day4_max_temp = models.IntegerField(verbose_name="Temperatura Máxima")
    day4_weather = models.CharField(
        max_length=10, choices=TIEMPO_CHOICES, verbose_name="Tiempo"
    )
    day5_date = models.DateField(verbose_name="Fecha")
    day5_min_temp = models.IntegerField(verbose_name="Temperatura Mínima")
    day5_max_temp = models.IntegerField(verbose_name="Temperatura Máxima")
    day5_weather = models.CharField(
        max_length=10, choices=TIEMPO_CHOICES, verbose_name="Tiempo"
    )
    lp = models.CharField(
        max_length=20, choices=LUNA_CHOICES, verbose_name="Fase Lunar"
    )
    nlp = models.CharField(
        max_length=20, choices=LUNA_CHOICES, verbose_name="Próxima Fase Lunar"
    )
    nlpd = models.DateField(verbose_name="Fecha Próxima Fase")
    sunrise = models.TimeField(verbose_name="Salida Sol")
    sunset = models.TimeField(verbose_name="Puesta Sol")
    uv_index = models.IntegerField(verbose_name="Índice UV")

    class Meta:
        verbose_name = "Pronóstico"
        verbose_name_plural = "Pronósticos"
        default_permissions = ()
        permissions = (
            ("view_forecast", "Ver"),
            ("add_forecast", "Añadir"),
            ("change_forecast", "Editar"),
            ("delete_forecast", "Eliminar"),
        )

    def __str__(self):
        return f"Pronóstico detallado - {self.date.strftime('%d/%m/%Y')}"


class BaseWarning(PDFModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    summary = models.TextField(max_length=300, verbose_name="Resumen")
    # El campo 'file' ya está heredado de PDFModel
    valid_until = models.DateTimeField(verbose_name="Válido Hasta")
    date = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha y Hora de Creación"
    )
    email_recipient_list = models.ForeignKey(
        "EmailRecipientList",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Lista de Correos",
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.summary


class EarlyWarning(BaseWarning):
    class Meta:
        verbose_name = "Aviso de Alerta Temprana"
        verbose_name_plural = "Avisos de Alertas Tempranas"
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
        default_permissions = ()
        permissions = (
            ("view_storm_warning", "Ver"),
            ("add_storm_warning", "Añadir"),
            ("change_storm_warning", "Editar"),
            ("delete_storm_warning", "Eliminar"),
        )


class Customer(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    company_name = models.CharField(max_length=100, verbose_name="Nombre de la Empresa")
    reeup = models.CharField(max_length=11, verbose_name="REEUP")
    nit = models.CharField(max_length=11, verbose_name="NIT")
    account = models.CharField(max_length=16, verbose_name="Cuenta Bancaria")
    address = models.TextField(verbose_name="Dirección")
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario")
    phone = models.CharField(max_length=8, verbose_name="Número de Teléfono")
    
    # Campos para suscripciones/notificaciones
    accept_terms = models.BooleanField(default=False, verbose_name="Aceptó Términos")
    newsletter = models.BooleanField(default=False, verbose_name="Recibe Newsletter")

    def __str__(self):
        return self.company_name

    def delete(self, *args, **kwargs):
        user = self.user
        super().delete(*args, **kwargs)
        user.delete()

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        default_permissions = ()
        permissions = (
            ("view_customer", "Ver"),
            ("add_customer", "Añadir"),
            ("change_customer", "Editar"),
            ("delete_customer", "Eliminar"),
        )


class Service(PDFModel):
    PUBLIC = "public"
    COMMERCIAL = "commercial"
    SERVICE_TYPE_CHOICES = [
        (PUBLIC, "Público"),
        (COMMERCIAL, "Comercial"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Usuario",
        related_name="created_services",
    )
    title = models.CharField(max_length=100, verbose_name="Título")
    summary = models.CharField(max_length=300, verbose_name="Resumen")
    # El campo 'file' ya está heredado de PDFModel
    service_type = models.CharField(
        max_length=10,
        choices=SERVICE_TYPE_CHOICES,
        default=PUBLIC,
        verbose_name="Tipo de Servicio",
    )
    target_customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        verbose_name="Cliente Destinatario",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.title

    def clean(self):
        if self.service_type == Service.COMMERCIAL and not self.target_customer:
            raise ValidationError("Cliente obligatorio para servicios comerciales.")

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        default_permissions = ()
        permissions = (
            ("view_service", "Ver"),
            ("add_service", "Añadir"),
            ("change_service", "Editar"),
            ("delete_service", "Eliminar"),
        )


class WeatherToday(PDFModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Autor")
    date = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha y Hora de Creación"
    )
    summary = models.TextField(max_length=300, verbose_name="Resumen")
    # El campo 'file' ya está heredado de PDFModel
    email_recipient_list = models.ForeignKey(
        "EmailRecipientList",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Lista de Correos",
    )

    def __str__(self):
        return f"Pronóstico del tiempo detallado para {self.date}"

    class Meta:
        verbose_name = "Tiempo Hoy"
        verbose_name_plural = "Tiempo Hoy"
        default_permissions = ()
        permissions = (
            ("view_weather_today", "Ver"),
            ("add_weather_today", "Añadir"),
            ("change_weather_today", "Editar"),
            ("delete_weather_today", "Eliminar"),
        )


class WeatherTomorrow(PDFModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Autor")
    date = models.DateTimeField(verbose_name="Fecha y Hora de Creación")
    summary = models.CharField(max_length=300, verbose_name="Resumen")
    # El campo 'file' ya está heredado de PDFModel
    email_recipient_list = models.ForeignKey(
        "EmailRecipientList",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Lista de Correos",
    )

    def __str__(self):
        return f"Pronóstico del tiempo detallado para {self.date}"

    class Meta:
        verbose_name = "Tiempo Mañana"
        verbose_name_plural = "Tiempo Mañana"
        default_permissions = ()
        permissions = (
            ("view_weather_tomorrow", "Ver"),
            ("add_weather_tomorrow", "Añadir"),
            ("change_weather_tomorrow", "Editar"),
            ("delete_weather_tomorrow", "Eliminar"),
        )


class WeatherCommentary(PDFModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Autor")
    date = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha y Hora de Creación"
    )
    summary = models.CharField(max_length=300, verbose_name="Resumen")
    # El campo 'file' ya está heredado de PDFModel
    email_recipient_list = models.ForeignKey(
        "EmailRecipientList",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Lista de Correos",
    )

    def __str__(self):
        return f"Comentario del tiempo detallado para {self.date}"

    class Meta:
        verbose_name = "Comentario del Tiempo"
        verbose_name_plural = "Comentarios del Tiempo"
        default_permissions = ()
        permissions = (
            ("view_weather_commentary", "Ver"),
            ("add_weather_commentary", "Añadir"),
            ("change_weather_commentary", "Editar"),
            ("delete_weather_commentary", "Eliminar"),
        )


class WeatherNote(PDFModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Autor")
    date = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha y Hora de Creación"
    )
    summary = models.CharField(max_length=300, verbose_name="Resumen")
    # El campo 'file' ya está heredado de PDFModel
    email_recipient_list = models.ForeignKey(
        "EmailRecipientList",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Lista de Correos",
    )

    def __str__(self):
        return f"Nota Meteorológica detallada para {self.date}"

    class Meta:
        verbose_name = "Nota Meteorológica"
        verbose_name_plural = "Notas Meteorológicas"
        default_permissions = ()
        permissions = (
            ("view_weather_note", "Ver"),
            ("add_weather_note", "Añadir"),
            ("change_weather_note", "Editar"),
            ("delete_weather_note", "Eliminar"),
        )


class EmailRecipientList(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(
        max_length=100, unique=True, verbose_name="Nombre de la Lista"
    )
    description = models.TextField(blank=True, verbose_name="Descripción")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Lista de Correo"
        verbose_name_plural = "Listas de Correo"
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
    recipient_list = models.ForeignKey(
        EmailRecipientList,
        on_delete=models.CASCADE,
        related_name="recipients",
        verbose_name="Lista de Correo",
    )

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Destinatario de Correo"
        verbose_name_plural = "Destinatarios de Correo"
        default_permissions = ()
        permissions = (
            ("view_email_recipient", "Ver"),
            ("add_email_recipient", "Añadir"),
            ("change_email_recipient", "Editar"),
            ("delete_email_recipient", "Eliminar"),
        )


class ScientificPublication(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=200, verbose_name="Título")
    author = models.ForeignKey(
        "Author",
        on_delete=models.CASCADE,
        related_name="authored_publications",
        verbose_name="Autor",
    )
    coauthors = models.ManyToManyField(
        "Author",
        related_name="coauthored_publications",
        verbose_name="Coautores",
        blank=True,
    )
    publication_date = models.DateField(verbose_name="Fecha de Publicación")
    summary = models.TextField(verbose_name="Resumen")
    pdf_file = models.FileField(
        upload_to="publications/pdf/",
        validators=[FileExtensionValidator(["pdf"])],
        verbose_name="Archivo PDF",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Fecha de Actualización"
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Publicación Científica"
        verbose_name_plural = "Publicaciones Científicas"
        ordering = ["-publication_date"]
        default_permissions = ()
        permissions = (
            ("view_scientific_publication", "Ver"),
            ("add_scientific_publication", "Añadir"),
            ("change_scientific_publication", "Editar"),
            ("delete_scientific_publication", "Eliminar"),
        )


class Author(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    first_name = models.CharField(max_length=100, verbose_name="Nombres")
    last_name = models.CharField(max_length=100, verbose_name="Apellidos")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    institution = models.CharField(
        max_length=200, blank=True, verbose_name="Institución"
    )
    orcid_id = models.CharField(max_length=19, blank=True, verbose_name="ID ORCID")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Autor"
        verbose_name_plural = "Autores"
        ordering = ["last_name", "first_name"]
        default_permissions = ()
        permissions = (
            ("view_author", "Ver"),
            ("add_author", "Añadir"),
            ("change_author", "Editar"),
            ("delete_author", "Eliminar"),
        )
