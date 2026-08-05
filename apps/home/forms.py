from datetime import datetime

from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator

from apps.meteo.models import Town


class MeteoDataForm(forms.Form):
    VAR_CHOICES = [
        ('T2', 'Temperatura a 2m (°C)'),
        ('td2', 'Punto de Rocío a 2m (°C)'),
        ('rh2', 'Humedad Relativa a 2m (%)'),
        ('RAINC', 'Precipitación Acumulada (mm)'),
        ('RAINC3H', 'Precipitación Acumulada cada 3 horas (mm)'),
        ('slp', 'Presión a Nivel del Mar (hPa)'),
        ('PSFC', 'Presión en Superficie (hPa)'),
        ('ws10', 'Velocidad del Viento a 10m (km/h)'),
        ('wd10', 'Dirección del Viento a 10m (grados)'),
        ('clflo', 'Fracción de Nubes Bajas (%)'),
        ('clfmi', 'Fracción de Nubes Medias (%)'),
        ('clfhi', 'Fracción de Nubes Altas (%)'),
        ('mcape', 'MCAPE (J/kg)'),
        ('mcin', 'MCIN (J/kg)'),
        ('lcl', 'Nivel de Condensación por Ascenso (m)'),
        ('lfc', 'Nivel de Libre Convección (m)'),
        ('NOAHRES', 'Balance de Energía Residual NOAH (W/m²)'),
        ('SWDOWN', 'Radiación Solar Incidente (W/m²)'),
        ('GLW', 'Radiación Infrarroja Incidente (W/m²)'),
        ('SWNORM', 'Radiación Solar Normal (W/m²)'),
        ('OLR', 'Radiación Infrarroja Saliente (W/m²)'),
    ]

    datetime_init = forms.CharField(
        label='Fecha y hora inicial (YYYYMMDDHH)',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Ej. 2025071006',
                'pattern': r'\d{10}',
                'title': 'Ingrese fecha en formato YYYYMMDDHH',
            }
        ),
    )

    var_name = forms.ChoiceField(label='Variable Meteorológica', choices=VAR_CHOICES)

    def clean_datetime_init(self):
        data = self.cleaned_data['datetime_init']
        try:
            datetime.strptime(data, '%Y%m%d%H')
        except ValueError:
            raise forms.ValidationError('Formato debe ser YYYYMMDDHH') from None
        return data

    def clean(self):
        cleaned_data = super().clean()
        var_name = cleaned_data.get('var_name')

        # Validaciones específicas por variable
        if var_name in ['rh2', 'clflo', 'clfmi', 'clfhi']:
            # Aquí podrías validar que los datos estén en el rango 0-100
            pass

        return cleaned_data


class MeteogramForm(forms.Form):
    datetime_init = forms.CharField(
        label='Fecha y hora inicial',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'YYYYMMDDHH', 'pattern': r'\d{10}'}
        ),
        help_text='Formato: AAAAMMDDHH (ej. 2025071806 para el 18 de julio 2025 a las 06:00)',
    )

    town = forms.ModelChoiceField(
        queryset=Town.objects.all().order_by('name'),
        label='Municipio',
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Seleccione un municipio',
    )

    def clean_datetime_init(self):
        data = self.cleaned_data['datetime_init']
        try:
            datetime.strptime(data, '%Y%m%d%H')
        except ValueError:
            raise forms.ValidationError('Formato debe ser YYYYMMDDHH') from None
        return data


class SoundingForm(forms.Form):
    datetime_init = forms.CharField(
        label='Fecha y hora inicial',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'YYYYMMDDHH', 'pattern': r'\d{10}'}
        ),
        help_text='Formato: AAAAMMDDHH (ej. 2025071806 para el 18 de julio 2025 a las 06:00)',
    )

    town = forms.ModelChoiceField(
        queryset=Town.objects.all().order_by('name'),
        label='Municipio',
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Seleccione un municipio',
    )

    t_index = forms.IntegerField(
        label='Índice de tiempo',
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '24'}),
        validators=[MinValueValidator(1), MaxValueValidator(24)],
        help_text='Índice de tiempo (1-24) para el pronóstico',
    )

    def clean_datetime_init(self):
        data = self.cleaned_data['datetime_init']
        try:
            datetime.strptime(data, '%Y%m%d%H')
        except ValueError:
            raise forms.ValidationError('Formato debe ser YYYYMMDDHH') from None
        return data


class GifDownloadForm(forms.Form):
    """Formulario para descargar GIF animado con rango personalizado"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Establecer valores por defecto si no se proporcionan
        if not self.initial.get('fecha_inicio'):
            self.initial['fecha_inicio'] = self.get_default_start_date()
        if not self.initial.get('fecha_fin'):
            self.initial['fecha_fin'] = self.get_default_end_date()

    fecha_inicio = forms.CharField(
        label='Fecha inicial del rango (YYYYMMDDHH)',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Ej. 2025102900',
                'pattern': r'\d{10}',
                'title': 'Ingrese fecha en formato YYYYMMDDHH',
            }
        ),
        required=True,
    )

    fecha_fin = forms.CharField(
        label='Fecha final del rango (YYYYMMDDHH)',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Ej. 2025102918',
                'pattern': r'\d{10}',
                'title': 'Ingrese fecha en formato YYYYMMDDHH',
            }
        ),
        required=True,
    )

    def get_default_start_date(self):
        """Obtener fecha inicial por defecto (fecha actual a las 00:00)"""
        now = datetime.now()
        return now.strftime('%Y%m%d00')

    def get_default_end_date(self):
        """Obtener fecha final por defecto (fecha actual + 18 horas)"""
        now = datetime.now()
        # Agregar 18 horas para un rango por defecto de 18 horas (dentro del límite de 3 días)
        future_date = now.replace(hour=18, minute=0, second=0, microsecond=0)
        return future_date.strftime('%Y%m%d18')

    def clean_fecha_inicio(self):
        data = self.cleaned_data['fecha_inicio']
        try:
            datetime.strptime(data, '%Y%m%d%H')
        except ValueError:
            raise forms.ValidationError('Formato debe ser YYYYMMDDHH') from None
        return data

    def clean_fecha_fin(self):
        data = self.cleaned_data['fecha_fin']
        try:
            datetime.strptime(data, '%Y%m%d%H')
        except ValueError:
            raise forms.ValidationError('Formato debe ser YYYYMMDDHH') from None
        return data

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin:
            fecha_ini_dt = datetime.strptime(fecha_inicio, '%Y%m%d%H')
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y%m%d%H')

            if fecha_ini_dt > fecha_fin_dt:
                raise forms.ValidationError(
                    'La fecha de inicio no puede ser mayor que la fecha final'
                )

            # Validar que el rango no sea mayor a 3 días (72 horas)
            diferencia = fecha_fin_dt - fecha_ini_dt
            if diferencia.total_seconds() > 72 * 3600:  # 72 horas en segundos
                raise forms.ValidationError('El rango máximo permitido es de 3 días (72 horas)')

        return cleaned_data
