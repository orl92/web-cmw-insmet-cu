from django import forms

from dashboard.models import *


class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField()


class ForecastsForm(forms.ModelForm):
    class Meta:
        model = Forecasts
        fields = '__all__'
