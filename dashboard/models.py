import uuid
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from common.utils import ImageModel, generic_pdf_path


# Create your models here.

class SiteConfiguration(models.Model):
    id = models.AutoField(primary_key=True)  # ID predeterminado de Django
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)  # Identificador único adicional
    maintenance_mode = models.BooleanField(default=True)  # Modo de mantenimiento activado por defecto

    class Meta:
        verbose_name = "Configuración del Sitio"
        verbose_name_plural = "Configuraciones del Sitio"

    def __str__(self):
        return f"Modo Mantenimiento: {'Activado' if self.maintenance_mode else 'Desactivado'}"

TIEMPO_CHOICES = [
    ('PN', 'PN'),  # Poco Nublado
    ('PARCN', 'PARCN'),  # Parcialmente Nublado
    ('N', 'N'),  # Nublado
    ('AIS CHUB', 'AIS CHUB'),  # Aislados Chubascos
    ('ALG CHUB', 'ALG CHUB'),  # Algunos Chubascos
    ('NUM CHUB', 'NUM CHUB'),  # Numerosos Chubascos
    ('ALG TORM', 'ALG TORM'),  # Algunas Tormentas
    ('NUM TORM', 'NUM TORM'),  # Numerosas Tormentas
]

VIENTO_DIRECCION_CHOICES = [
    ('VRB', 'VRB'),  # Variable Debil
    ('N', 'N'),  # Norte
    ('NNE', 'NNE'),  # Norte Noreste
    ('NE', 'NE'),  # Noreste
    ('ENE', 'ENE'),  # Este Noreste
    ('E', 'E'),  # Este
    ('ESE', 'ESE'),  # Este Sureste
    ('SE', 'SE'),  # Sureste
    ('SSE', 'SSE'),  # Sur Sureste
    ('S', 'S'),  # Sur
    ('SSW', 'SSW'),  # Sur Suroeste
    ('SW', 'SW'),  # Suroeste
    ('WSW', 'WSW'),  # Oeste Suroeste
    ('W', 'W'),  # Oeste
    ('WNW', 'WNW'),  # Oeste Noroeste
    ('NW', 'NW'),  # Noroeste
    ('NNW', 'NNW'),  # Norte Noroeste
]

LUNA_CHOICES = [
    ('Luna Nueva', 'Luna Nueva'),
    ('Creciente', 'Creciente'),
    ('Cuarto Creciente', 'Cuarto Creciente'),
    ('Gibosa Creciente', 'Gibosa Creciente'),
    ('Luna Llena', 'Luna Llena'),
    ('Gibosa Menguante', 'Gibosa Menguante'),
    ('Cuarto Menguante', 'Cuarto Menguante'),
    ('Menguante', 'Menguante'),  
]

MAR_CHOICES = [
    ('TQ', 'TQ'),  # Tranquila
    ('PO', 'PO'),  # Poco Oleaje
    ('O', 'O'),  # Oleaje
    ('MRJ', 'MRJ'),  # Marejadas
    ('FMRJ', 'FMRJ'),  # Fuertes Marejadas
]

class Province(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=15, verbose_name='Nombre')
    code = models.CharField(max_length=5, unique=True, verbose_name='Código')

    class Meta:
        verbose_name = 'Provincia'
        verbose_name_plural = "Provincias"
        default_permissions = ()
        permissions = (
            ('view_province', 'Ver'),
            ('add_province', 'Añadir'),
            ('change_province', 'Editar'),
            ('delete_province', 'Eliminar'),
        )

    def __str__(self):
        return self.name

class Station(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True, related_name="stations", 
                                 verbose_name='Provincia')
    name = models.CharField(max_length=15, verbose_name='Nombre')
    number = models.IntegerField(unique=True, verbose_name='Número')
    latitude = models.FloatField(verbose_name='Latitud')
    longitude = models.FloatField(verbose_name='Longitud')

    class Meta:
        verbose_name = 'Estación'
        verbose_name_plural = "Estaciones"
        default_permissions = ()
        permissions = (
            ('view_station', 'Ver'),
            ('add_station', 'Añadir'),
            ('change_station', 'Editar'),
            ('delete_station', 'Eliminar'),
        )

    def __str__(self):
        return self.name

class Forecasts(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date = models.DateField(verbose_name='Fecha', unique=True, db_index=True)
    ntm = models.IntegerField(verbose_name='Temperatura Mañana')
    nta = models.IntegerField(verbose_name='Temperatura Tarde (Max)')
    ntn = models.IntegerField(verbose_name='Temperatura Noche')
    nwm = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo Mañana')
    nwa = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo Tarde')
    nwn = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo Noche')
    nwddm = models.CharField(max_length=10, choices=VIENTO_DIRECCION_CHOICES,
                             verbose_name='Dirección del Viento Mañana')
    nwdda = models.CharField(max_length=10, choices=VIENTO_DIRECCION_CHOICES,
                             verbose_name='Dirección del Viento Tarde')
    nwddn = models.CharField(max_length=10, choices=VIENTO_DIRECCION_CHOICES,
                             verbose_name='Dirección del Viento Noche')
    nwdfm = models.CharField(max_length=5, verbose_name='Velocidad del Viento Mañana')
    nwdfa = models.CharField(max_length=5, verbose_name='Velocidad del Viento Tarde')
    nwdfn = models.CharField(max_length=5, verbose_name='Velocidad del Viento Noche')
    nsm = models.CharField(max_length=10, choices=MAR_CHOICES, verbose_name='Mar Mañana')
    nsa = models.CharField(max_length=10, choices=MAR_CHOICES, verbose_name='Mar Tarde')
    nsn = models.CharField(max_length=10, choices=MAR_CHOICES, verbose_name='Mar Noche')
    itm = models.IntegerField(verbose_name='Temperatura Mañana')
    ita = models.IntegerField(verbose_name='Temperatura Tarde (Max)')
    itn = models.IntegerField(verbose_name='Temperatura Noche')
    iwm = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo Mañana')
    iwa = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo Tarde')
    iwn = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo Noche')
    iwddm = models.CharField(max_length=10, choices=VIENTO_DIRECCION_CHOICES,
                             verbose_name='Dirección del Viento Mañana')
    iwdda = models.CharField(max_length=10, choices=VIENTO_DIRECCION_CHOICES,
                             verbose_name='Dirección del Viento Tarde')
    iwddn = models.CharField(max_length=10, choices=VIENTO_DIRECCION_CHOICES,
                             verbose_name='Dirección del Viento Noche')
    iwdfm = models.CharField(max_length=5, verbose_name='Velocidad del Viento Mañana')
    iwdfa = models.CharField(max_length=5, verbose_name='Velocidad del Viento Tarde')
    iwdfn = models.CharField(max_length=5, verbose_name='Velocidad del Viento Noche')
    stm = models.IntegerField(verbose_name='Temperatura Mañana')
    sta = models.IntegerField(verbose_name='Temperatura Tarde (Max)')
    stn = models.IntegerField(verbose_name='Temperatura Noche')
    swm = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo Mañana')
    swa = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo Tarde')
    swn = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo Noche')
    swddm = models.CharField(max_length=10, choices=VIENTO_DIRECCION_CHOICES,
                             verbose_name='Dirección del Viento Mañana')
    swdda = models.CharField(max_length=10, choices=VIENTO_DIRECCION_CHOICES,
                             verbose_name='Dirección del Viento Tarde')
    swddn = models.CharField(max_length=10, choices=VIENTO_DIRECCION_CHOICES,
                             verbose_name='Dirección del Viento Noche')
    swdfm = models.CharField(max_length=5, verbose_name='Velocidad del Viento Mañana')
    swdfa = models.CharField(max_length=5, verbose_name='Velocidad del Viento Tarde')
    swdfn = models.CharField(max_length=5, verbose_name='Velocidad del Viento Noche')
    ssm = models.CharField(max_length=10, choices=MAR_CHOICES, verbose_name='Mar Mañana')
    ssa = models.CharField(max_length=10, choices=MAR_CHOICES, verbose_name='Mar Tarde')
    ssn = models.CharField(max_length=10, choices=MAR_CHOICES, verbose_name='Mar Noche')
    day1_date = models.DateField(verbose_name='Fecha')
    day1_min_temp = models.IntegerField(verbose_name='Temperatura Mínima')
    day1_max_temp = models.IntegerField(verbose_name='Temperatura Máxima')
    day1_weather = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo')
    day2_date = models.DateField(verbose_name='Fecha')
    day2_min_temp = models.IntegerField(verbose_name='Temperatura Mínima')
    day2_max_temp = models.IntegerField(verbose_name='Temperatura Máxima')
    day2_weather = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo')
    day3_date = models.DateField(verbose_name='Fecha')
    day3_min_temp = models.IntegerField(verbose_name='Temperatura Mínima')
    day3_max_temp = models.IntegerField(verbose_name='Temperatura Máxima')
    day3_weather = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo')
    day4_date = models.DateField(verbose_name='Fecha')
    day4_min_temp = models.IntegerField(verbose_name='Temperatura Mínima')
    day4_max_temp = models.IntegerField(verbose_name='Temperatura Máxima')
    day4_weather = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo')
    day5_date = models.DateField(verbose_name='Fecha')
    day5_min_temp = models.IntegerField(verbose_name='Temperatura Mínima')
    day5_max_temp = models.IntegerField(verbose_name='Temperatura Máxima')
    day5_weather = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo')
    lp = models.CharField(max_length=20, choices=LUNA_CHOICES, verbose_name='Fase Lunar')
    nlp = models.CharField(max_length=20, choices=LUNA_CHOICES, verbose_name='Próxima Fase Lunar')
    nlpd = models.DateField(verbose_name='Fecha Próxima Fase')
    sunrise = models.TimeField(verbose_name='Salida Sol')
    sunset = models.TimeField(verbose_name='Puesta Sol')
    uv_index = models.IntegerField(verbose_name='Índice UV')

    class Meta:
        verbose_name = 'Pronóstico'
        verbose_name_plural = "Pronósticos"
        default_permissions = ()
        permissions = (
            ('view_forecast', 'Ver'),
            ('add_forecast', 'Añadir'),
            ('change_forecast', 'Editar'),
            ('delete_forecast', 'Eliminar'),
        )

    def __str__(self): 
        return f"Pronóstico detallado - {self.date.strftime('%d/%m/%Y')}"

class BaseWarning(ImageModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=50, verbose_name='Título')
    subject = models.CharField(max_length=100, verbose_name='Asunto')
    date = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y Hora de Creación')
    valid_until = models.DateTimeField(verbose_name='Válido Hasta')
    description = models.TextField(verbose_name='Descripción')
    email_recipient_list = models.ForeignKey(
        'EmailRecipientList',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Lista de Correos"
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.title

class EarlyWarning(BaseWarning):

    class Meta:
        verbose_name = 'Aviso Alerta Temprana'
        verbose_name_plural = "Avisos Alertas Tempranas"
        default_permissions = ()
        permissions = (
            ('view_early_warning', 'Ver'),
            ('add_early_warning', 'Añadir'),
            ('change_early_warning', 'Editar'),
            ('delete_early_warning', 'Eliminar'),
        )

class TropicalCyclone(BaseWarning):

    class Meta:
        verbose_name = 'Aviso Ciclón Tropical'
        verbose_name_plural = "Avisos Ciclones Tropicales"
        default_permissions = ()
        permissions = (
            ('view_tropical_cyclone', 'Ver'),
            ('add_tropical_cyclone', 'Añadir'),
            ('change_tropical_cyclone', 'Editar'),
            ('delete_tropical_cyclone', 'Eliminar'),
        )

class SpecialNotice(BaseWarning):

    class Meta:
        verbose_name = 'Aviso Especial'
        verbose_name_plural = "Avisos Especiales"
        default_permissions = ()
        permissions = (
            ('view_special_notice', 'Ver'),
            ('add_special_notice', 'Añadir'),
            ('change_special_notice', 'Editar'),
            ('delete_special_notice', 'Eliminar'),
        )

class RadarWarning(BaseWarning):
    
    class Meta:
        verbose_name = 'Aviso Radar'
        verbose_name_plural = "Avisos Radares"
        default_permissions = ()
        permissions = (
            ('view_radar_warning', 'Ver'),
            ('add_radar_warning', 'Añadir'),
            ('change_radar_warning', 'Editar'),
            ('delete_radar_warning', 'Eliminar'),
        )

class Customer(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    company_name = models.CharField(max_length=100, verbose_name='Nombre de la Empresa')
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Usuario')
    
    def __str__(self):
        return self.company_name
    
    def delete(self, *args, **kwargs):
        user = self.user
        super().delete(*args, **kwargs)
        user.delete()

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = "Clientes"
        default_permissions = ()
        permissions = (
            ('view_customer', 'Ver'),
            ('add_customer', 'Añadir'),
            ('change_customer', 'Editar'),
            ('delete_customer', 'Eliminar'),
        )

class Service(models.Model):
    PUBLIC = 'public'
    COMMERCIAL = 'commercial'
    SERVICE_TYPE_CHOICES = [
        (PUBLIC, 'Público'),
        (COMMERCIAL, 'Comercial'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuario', related_name='created_services')
    title = models.CharField(max_length=100, verbose_name='Título')
    summary = models.CharField(max_length=300, verbose_name='Resumen')
    file = models.FileField(upload_to=generic_pdf_path, verbose_name='PDF')
    service_type = models.CharField(
        max_length=10,
        choices=SERVICE_TYPE_CHOICES,
        default=PUBLIC,
        verbose_name='Tipo de Servicio'
    )
    target_customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='Cliente Destinatario', null=True, blank=True)

    def __str__(self):
        return self.title
    
    def clean(self):
        if self.service_type == Service.COMMERCIAL and not self.target_customer:
            raise ValidationError("Cliente obligatorio para servicios comerciales.")

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = "Servicios"
        default_permissions = ()
        permissions = (
            ('view_service', 'Ver'),
            ('add_service', 'Añadir'),
            ('change_service', 'Editar'),
            ('delete_service', 'Eliminar'),
        )

class WeatherToday(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Autor')
    date = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y Hora de Creación')
    summary = models.TextField(max_length=300, verbose_name='Resumen') 
    detailed_forecast = models.TextField(verbose_name='Pronóstico Detallado')
    email_recipient_list = models.ForeignKey(
        'EmailRecipientList',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Lista de Correos"
    )

    def __str__(self): 
        return f"Pronóstico del tiempo detallado para {self.date}"

    class Meta:
        verbose_name = 'Tiempo Hoy'
        default_permissions = ()
        permissions = (
            ('view_weather_today', 'Ver'),
            ('add_weather_today', 'Añadir'),
            ('change_weather_today', 'Editar'),
            ('delete_weather_today', 'Eliminar'),
        )

class WeatherTomorrow(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Autor')
    date = models.DateTimeField(verbose_name='Fecha y Hora de Creación')
    summary = models.CharField(max_length=300, verbose_name='Resumen') 
    detailed_forecast = models.TextField(verbose_name='Pronóstico Detallado')
    email_recipient_list = models.ForeignKey(
        'EmailRecipientList',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Lista de Correos"
    )

    def __str__(self): 
        return f"Pronóstico del tiempo detallado para {self.date}"

    class Meta:
        verbose_name = 'Tiempo Mañana'
        default_permissions = ()
        permissions = (
            ('view_weather_tomorrow', 'Ver'),
            ('add_weather_tomorrow', 'Añadir'),
            ('change_weather_tomorrow', 'Editar'),
            ('delete_weather_tomorrow', 'Eliminar'),
        )

class WeatherCommentary(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Autor')
    date = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y Hora de Creación')
    subject = models.CharField(max_length=300, verbose_name='Asunto') 
    detailed_commentary = models.TextField(verbose_name='Comentario Detallado')
    email_recipient_list = models.ForeignKey(
        'EmailRecipientList',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Lista de Correos"
    )

    def __str__(self): 
        return f"Comentario del tiempo detallado para {self.date}"

    class Meta:
        verbose_name = 'Comentario del Tiempo'
        default_permissions = ()
        permissions = (
            ('view_weather_commentary', 'Ver'),
            ('add_weather_commentary', 'Añadir'),
            ('change_weather_commentary', 'Editar'),
            ('delete_weather_commentary', 'Eliminar'),
        )

class WeatherNote(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Autor')
    date = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y Hora de Creación')
    subject = models.CharField(max_length=300, verbose_name='Asunto') 
    detailed_note = models.TextField(verbose_name='Nota Detallada')
    email_recipient_list = models.ForeignKey(
        'EmailRecipientList',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Lista de Correos"
    )

    def __str__(self): 
        return f"Nota Meteorológica detallada para {self.date}"

    class Meta:
        verbose_name = 'Nota Meteorológica'
        default_permissions = ()
        permissions = (
            ('view_weather_note', 'Ver'),
            ('add_weather_note', 'Añadir'),
            ('change_weather_note', 'Editar'),
            ('delete_weather_note', 'Eliminar'),
        )

class EmailRecipientList(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Lista")
    description = models.TextField(blank=True, verbose_name="Descripción")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Lista de Correo'
        verbose_name_plural = "Lista de Correos"
        default_permissions = ()
        permissions = (
            ('view_email_recipient_list', 'Ver'),
            ('add_email_recipient_list', 'Añadir'),
            ('change_email_recipient_list', 'Editar'),
            ('delete_email_recipient_list', 'Eliminar'),
        )

class EmailRecipient(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True, verbose_name="Correo Electrónico")
    recipient_list = models.ForeignKey(
        EmailRecipientList, on_delete=models.CASCADE, related_name="recipients", verbose_name="Lista de Correo"
    )

    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name = 'Destinatario de Correo'
        verbose_name_plural = "Destinatarios de Correo"
        default_permissions = ()
        permissions = (
            ('view_email_recipient', 'Ver'),
            ('add_email_recipient', 'Añadir'),
            ('change_email_recipient', 'Editar'),
            ('delete_email_recipient', 'Eliminar'),
        )
