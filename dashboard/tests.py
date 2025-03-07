from django.db import models
from django.test import TestCase

# Create your tests here.




# Create your models here.

TIEMPO_CHOICES = [
    ('PN', 'Poco Nublado'),
    ('PARCN', 'Parcialmente Nublado'),
    ('N', 'Nublado'),
    ('AIS CHUB', 'Aislados Chubascos'),
    ('ALG CHUB', 'Algunos Chubascos'),
    ('NUM CHUB', 'Numerosos Chubascos'),
    ('ALG TORM', 'Algunas Tormentas'),
    ('NUM TORM', 'Numerosas Tormentas'),
]

VIENTO_DIRECCION_CHOICES = [
    ('VRB', '⭕ Variable'),
    ('N', '⬆ Norte'),
    ('NNE', '↗ Norte-Noreste'),
    ('NE', '↗ Noreste'),
    ('ENE', '➡ Este-Noreste'),
    ('E', '➡ Este'),
    ('ESE', '➡ Este-Sureste'),
    ('SE', '↘ Sureste'),
    ('SSE', '↘ Sur-Sureste'),
    ('S', '⬇ Sur'),
    ('SSW', '↙ Sur-Suroeste'),
    ('SW', '↙ Suroeste'),
    ('WSW', '⬅ Oeste-Suroeste'),
    ('W', '⬅ Oeste'),
    ('WNW', '⬅ Oeste-Noroeste'),
    ('NW', '↖ Noroeste'),
    ('NNW', '↖ Norte-Noroeste'),
]

LUNA_CHOICES = [
    ('LL', 'Luna Llena'),
    ('CC', 'Cuarto Creciente'),
    ('CM', 'Cuarto Menguante'),
    ('LN', 'Luna Nueva'),
    ('AUTO', 'AUTO'),
]

MAR_CHOICES = [
    ('TQ', 'TQ'),
    ('PO', 'PO'),
    ('O', 'O'),
    ('MRJ', 'MRJ'),
    ('FMRJ', 'FMRJ'),
]


class Province(models.Model):
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
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True, related_name="provinces",
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


class Forecast(models.Model):
    temperature_morning = models.IntegerField(verbose_name='Temperatura Mañana')
    temperature_afternoon = models.IntegerField(verbose_name='Temperatura Tarde (Max)')
    temperature_night = models.IntegerField(verbose_name='Temperatura Noche')
    weather_morning = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo Mañana')
    weather_afternoon = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo Tarde')
    weather_night = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo Noche')
    wind_direction_morning = models.CharField(max_length=10, choices=VIENTO_DIRECCION_CHOICES,
                                              verbose_name='Dirección del Viento Mañana')
    wind_direction_afternoon = models.CharField(max_length=10, choices=VIENTO_DIRECCION_CHOICES,
                                                verbose_name='Dirección del Viento Tarde')
    wind_direction_night = models.CharField(max_length=10, choices=VIENTO_DIRECCION_CHOICES,
                                            verbose_name='Dirección del Viento Noche')
    wind_force_morning = models.CharField(max_length=5, verbose_name='Velocidad del Viento Mañana')
    wind_force_afternoon = models.CharField(max_length=5, verbose_name='Velocidad del Viento Tarde')
    wind_force_night = models.CharField(max_length=5, verbose_name='Velocidad del Viento Noche')

    class Meta:
        abstract = True


class ForecastFecha(models.Model):
    all_forecasts = models.ForeignKey('AllForecasts', on_delete=models.CASCADE, related_name='forecasts_fecha')
    date = models.DateField(verbose_name='Fecha', unique=True)

    class Meta:
        verbose_name = 'Fecha'
        verbose_name_plural = 'Fechas'

    def __str__(self):
        return str(self.date)


class AllForecasts(models.Model):
    def get_date(self):
        forecast_fecha = self.forecast_fecha.first()
        if forecast_fecha is not None:
            return forecast_fecha.date
        return 'No hay pronósticos'

    class Meta:
        verbose_name = 'Pronóstico'
        verbose_name_plural = "Pronósticos"


class ForecastNorte(Forecast):
    all_forecasts = models.ForeignKey(AllForecasts, on_delete=models.CASCADE, related_name='forecasts_norte')
    sea_morning = models.CharField(max_length=10, choices=MAR_CHOICES, verbose_name='Mar Mañana')
    sea_afternoon = models.CharField(max_length=10, choices=MAR_CHOICES, verbose_name='Mar Tarde')
    sea_night = models.CharField(max_length=10, choices=MAR_CHOICES, verbose_name='Mar Noche')

    class Meta:
        verbose_name = 'Costa Norte'
        verbose_name_plural = 'Costa Norte'

    def __str__(self):
        return f"Costa Norte: {self.id}"


class ForecastSur(Forecast):
    all_forecasts = models.ForeignKey(AllForecasts, on_delete=models.CASCADE, related_name='forecasts_sur')
    sea_morning = models.CharField(max_length=10, choices=MAR_CHOICES, verbose_name='Mar Mañana')
    sea_afternoon = models.CharField(max_length=10, choices=MAR_CHOICES, verbose_name='Mar Tarde')
    sea_night = models.CharField(max_length=10, choices=MAR_CHOICES, verbose_name='Mar Noche')

    class Meta:
        verbose_name = 'Costa Sur'
        verbose_name_plural = 'Costa Sur'

    def __str__(self):
        return f"Costa Sur: {self.id}"


class ForecastInterior(Forecast):
    all_forecasts = models.ForeignKey(AllForecasts, on_delete=models.CASCADE, related_name='forecasts_interior')

    class Meta:
        verbose_name = 'Interior'
        verbose_name_plural = 'Interior'

    def __str__(self):
        return f"Interior: {self.id}"


class ExtendedForecast(models.Model):
    all_forecasts = models.ForeignKey(AllForecasts, related_name='extended_forecasts', on_delete=models.CASCADE,
                                      verbose_name='Pronóstico')
    date = models.DateField(verbose_name='Fecha')
    min_temp = models.IntegerField(verbose_name='Temperatura Mínima')
    max_temp = models.IntegerField(verbose_name='Temperatura Máxima')
    weather = models.CharField(max_length=10, choices=TIEMPO_CHOICES, verbose_name='Tiempo')

    class Meta:
        verbose_name = 'Pronóstico Extendido'
        verbose_name_plural = "Pronósticos Extendidos"
        default_permissions = ()
        permissions = (
            ('view_extended_forecast', 'Ver'),
            ('add_extended_forecast', 'Añadir'),
            ('change_extended_forecast', 'Editar'),
            ('delete_extended_forecast', 'Eliminar'),
        )

    def __str__(self):
        return str(self.date)


class AstronomicalData(models.Model):
    all_forecasts = models.ForeignKey(AllForecasts, related_name='astronomical_datas', on_delete=models.CASCADE,
                                      verbose_name='Pronóstico')
    lunar_phase = models.CharField(max_length=20, choices=LUNA_CHOICES, verbose_name='Fase Lunar')
    next_lunar_phase = models.CharField(max_length=20, choices=LUNA_CHOICES, verbose_name='Próxima Fase Lunar')
    next_lunar_phase_date = models.DateField(verbose_name='Fecha Próxima Fase Lunar')
    sunrise = models.TimeField(verbose_name='Salida Sol')
    sunset = models.TimeField(verbose_name='Puesta Sol')
    uv_index = models.IntegerField(verbose_name='Índice UV')

    class Meta:
        verbose_name = 'Dato Astronómico'
        verbose_name_plural = "Datos Astronómicos"
        default_permissions = ()
        permissions = (
            ('view_astronomical_data', 'Ver'),
            ('add_astronomical_data', 'Añadir'),
            ('change_astronomical_data', 'Editar'),
            ('delete_astronomical_data', 'Eliminar'),
        )

    def __str__(self):
        return f"Astronomical: {self.id}"
