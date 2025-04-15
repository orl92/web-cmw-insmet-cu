import datetime

from django import forms

from dashboard.models import Forecasts


class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField()


class ForecastsForm(forms.ModelForm):
    class Meta:
        model = Forecasts
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'day1_date': forms.DateInput(attrs={'type': 'date'}),
            'day2_date': forms.DateInput(attrs={'type': 'date'}),
            'day3_date': forms.DateInput(attrs={'type': 'date'}),
            'day4_date': forms.DateInput(attrs={'type': 'date'}),
            'day5_date': forms.DateInput(attrs={'type': 'date'}),
            'nlpd': forms.DateInput(attrs={'type': 'date'}),
            'sunrise': forms.TimeInput(attrs={'type': 'time'}),
            'sunset': forms.TimeInput(attrs={'type': 'time'}),
        }
        
    def clean_date(self):
        date = self.cleaned_data.get('date')
        if isinstance(date, datetime.date):
            return date
        try:
            return datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            raise forms.ValidationError("Formato de fecha inválido. Use YYYY-MM-DD")
