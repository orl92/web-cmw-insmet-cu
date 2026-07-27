from django import forms

from apps.meteo.models import Province


class ProvinceForm(forms.ModelForm):
    class Meta:
        model = Province
        fields = ['name', 'code']
