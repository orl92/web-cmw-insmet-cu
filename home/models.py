from django.db import models

from common.utils import ImageModel


class Maps(ImageModel):
    TIPO_CHOICES = (
        ('TV', 'TV'),
        ('TRH', 'Tri horario'),
        ('S', 'Sinóptico'),
        ('SA', 'Sinóptico Atlantico'),
        ('F200', 'Vinto en 200 hPa'),
        ('F500', 'Vinto en 500 hPa'),
        ('F700', 'Vinto en 700 hPa'),
        ('F850', 'Vinto en 850 hPa'),
        ('N200', 'Nivel de 200 hPa'),
        ('N500', 'Nivel de 500 hPa'),
        ('N700', 'Nivel de 700 hPa'),
        ('N850', 'Nivel de 850 hPa'),
    )

    hour = models.CharField(max_length=2, verbose_name='Horario')
    type = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name='Tipo')

    class Meta:
       verbose_name = 'Mapa'
       verbose_name_plural = 'Mapas'