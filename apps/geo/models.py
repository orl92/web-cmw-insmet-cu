import uuid

from django.db import models


class Province(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=15, verbose_name="Nombre")
    code = models.CharField(max_length=5, unique=True, verbose_name="Código")

    class Meta:
        managed = False
        db_table = 'dashboard_province'
        verbose_name = "Provincia"
        verbose_name_plural = "Provincias"
        ordering = ('name',)
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
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True, related_name="towns", verbose_name="Provincia")
    name = models.CharField(max_length=25, verbose_name="Nombre")
    latitude = models.FloatField(verbose_name="Latitud")
    longitude = models.FloatField(verbose_name="Longitud")

    class Meta:
        managed = False
        db_table = 'dashboard_town'
        verbose_name = "Municipio"
        verbose_name_plural = "Municipios"
        ordering = ('name',)
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
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True, related_name="stations", verbose_name="Provincia")
    name = models.CharField(max_length=15, verbose_name="Nombre")
    number = models.IntegerField(unique=True, verbose_name="Número")
    latitude = models.FloatField(verbose_name="Latitud")
    longitude = models.FloatField(verbose_name="Longitud")

    class Meta:
        managed = False
        db_table = 'dashboard_station'
        verbose_name = "Estación"
        verbose_name_plural = "Estaciones"
        ordering = ('name',)
        default_permissions = ()
        permissions = (
            ("view_station", "Ver"),
            ("add_station", "Añadir"),
            ("change_station", "Editar"),
            ("delete_station", "Eliminar"),
        )

    def __str__(self):
        return self.name
