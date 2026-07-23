from django import forms

from apps.geo.models import Province


class ProvinceForm(forms.ModelForm):
    class Meta:
        model = Province
        fields = ['name', 'code']
