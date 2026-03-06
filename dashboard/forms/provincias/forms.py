from django import forms

from dashboard.models import Province


class ProvinceForm(forms.ModelForm):
    class Meta:
        model = Province
        fields = '__all__'