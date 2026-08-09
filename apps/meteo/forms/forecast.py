import datetime

from django import forms
from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet

from apps.meteo.models import ForecastExtendedDay, ForecastRegions, Forecasts

ForecastRegionsFormSet = inlineformset_factory(
    Forecasts,
    ForecastRegions,
    fields=['region', 'period', 'temp', 'weather', 'wind_dir', 'wind_speed', 'sea_note'],
    extra=9,
    max_num=9,
    can_delete=False,
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


class BaseForecastExtendedDayFormSet(BaseInlineFormSet):
    """Fuerza que la fecha de cada día extendido sea la del pronóstico + day_number."""

    def clean(self):
        super().clean()
        forecast = self.instance
        forecast_date = getattr(forecast, 'date', None)
        if not forecast or not forecast_date:
            return
        for form in self.forms:
            if not form.cleaned_data or form.errors:
                continue
            day_number = form.cleaned_data.get('day_number')
            date = form.cleaned_data.get('date')
            if not day_number or not date:
                continue
            expected = forecast_date + datetime.timedelta(days=int(day_number))
            if date != expected:
                form.add_error(
                    'date',
                    (
                        f'La fecha debe ser el día {day_number} después del pronóstico '
                        f'({expected.strftime("%d/%m/%Y")}).'
                    ),
                )


ForecastExtendedDayFormSet = inlineformset_factory(
    Forecasts,
    ForecastExtendedDay,
    fields=['day_number', 'date', 'min_temp', 'max_temp', 'weather'],
    extra=5,
    max_num=5,
    can_delete=False,
    formset=BaseForecastExtendedDayFormSet,
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
            'date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'
            ),
            'lp': forms.Select(attrs={'class': 'form-select'}),
            'nlp': forms.Select(attrs={'class': 'form-select'}),
            'nlpd': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'
            ),
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
            raise forms.ValidationError('Formato de fecha inválido. Use YYYY-MM-DD') from None
