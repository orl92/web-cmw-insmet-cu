from django import forms
from datetime import datetime
from django.core.validators import MinValueValidator, MaxValueValidator

from dashboard.models import Town


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
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej. 2025071006',
            'pattern': '\d{10}',
            'title': 'Ingrese fecha en formato YYYYMMDDHH'
        })
    )

    var_name = forms.ChoiceField(
        label='Variable Meteorológica',
        choices=VAR_CHOICES
    )

    def clean_datetime_init(self):
        data = self.cleaned_data['datetime_init']
        try:
            datetime.strptime(data, '%Y%m%d%H')
        except ValueError:
            raise forms.ValidationError("Formato debe ser YYYYMMDDHH")
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
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'YYYYMMDDHH',
            'pattern': '\d{10}'
        }),
        help_text='Formato: AAAAMMDDHH (ej. 2025071806 para el 18 de julio 2025 a las 06:00)'
    )
    
    town = forms.ModelChoiceField(
        queryset=Town.objects.all().order_by('name'),
        label='Municipio',
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Seleccione un municipio'
    )

    def clean_datetime_init(self):
        data = self.cleaned_data['datetime_init']
        try:
            datetime.strptime(data, '%Y%m%d%H')
        except ValueError:
            raise forms.ValidationError("Formato debe ser YYYYMMDDHH")
        return data
    
class SoundingForm(forms.Form):
    datetime_init = forms.CharField(
        label='Fecha y hora inicial',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'YYYYMMDDHH',
            'pattern': '\d{10}'
        }),
        help_text='Formato: AAAAMMDDHH (ej. 2025071806 para el 18 de julio 2025 a las 06:00)'
    )

    town = forms.ModelChoiceField(
        queryset=Town.objects.all().order_by('name'),
        label='Municipio',
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Seleccione un municipio'
    )

    t_index = forms.IntegerField(
        label='Índice de tiempo',
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '24'
        }),
        validators=[MinValueValidator(1), MaxValueValidator(24)],
        help_text='Índice de tiempo (1-24) para el pronóstico'
    )

    def clean_datetime_init(self):
        data = self.cleaned_data['datetime_init']
        try:
            datetime.strptime(data, '%Y%m%d%H')
        except ValueError:
            raise forms.ValidationError("Formato debe ser YYYYMMDDHH")
        return data