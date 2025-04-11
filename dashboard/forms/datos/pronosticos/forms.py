from django import forms
from dashboard.models import Forecasts
import datetime

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField()


class ForecastsForm(forms.ModelForm):
    class Meta:
        model = Forecasts
        fields = '__all__'
        
    def clean_date(self):
        date = self.cleaned_data.get('date')
        if isinstance(date, datetime.date):
            return date
        try:
            return datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            raise forms.ValidationError("Formato de fecha inválido. Use YYYY-MM-DD")
