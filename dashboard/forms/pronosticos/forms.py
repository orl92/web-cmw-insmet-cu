import datetime

from django import forms

from dashboard.models import Forecasts


class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField()


from django.forms import inlineformset_factory

from dashboard.models import ForecastExtendedDay, ForecastRegions, Forecasts


ForecastRegionsFormSet = inlineformset_factory(
    Forecasts, ForecastRegions,
    fields=['region', 'period', 'temp', 'weather', 'wind_dir', 'wind_speed', 'sea_note'],
    extra=9, max_num=9, can_delete=False,
    widgets={
        'region': forms.HiddenInput(),
        'period': forms.HiddenInput(),
        'temp': forms.NumberInput(attrs={'class': 'form-control'}),
        'weather': forms.Select(attrs={'class': 'form-select'}),
        'wind_dir': forms.Select(attrs={'class': 'form-select'}),
        'wind_speed': forms.TextInput(attrs={'class': 'form-control'}),
        'sea_note': forms.Select(attrs={'class': 'form-select'}),
    },
)

ForecastExtendedDayFormSet = inlineformset_factory(
    Forecasts, ForecastExtendedDay,
    fields=['day_number', 'date', 'min_temp', 'max_temp', 'weather'],
    extra=5, max_num=5, can_delete=False,
    widgets={
        'day_number': forms.HiddenInput(),
        'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        'min_temp': forms.NumberInput(attrs={'class': 'form-control'}),
        'max_temp': forms.NumberInput(attrs={'class': 'form-control'}),
        'weather': forms.Select(attrs={'class': 'form-select'}),
    },
)


class ForecastsForm(forms.ModelForm):
    class Meta:
        model = Forecasts
        fields = ['date', 'lp', 'nlp', 'nlpd', 'sunrise', 'sunset', 'uv_index']
        widgets = {
        'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'lp': forms.Select(attrs={'class': 'form-select'}),
            'nlp': forms.Select(attrs={'class': 'form-select'}),
            'nlpd': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'sunrise': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'sunset': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'uv_index': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        
    def clean_date(self):
        date = self.cleaned_data.get('date')
        if isinstance(date, datetime.date):
            return date
        try:
            return datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            raise forms.ValidationError("Formato de fecha inválido. Use YYYY-MM-DD")
