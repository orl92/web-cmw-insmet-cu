from django import forms

from dashboard.models import Town


class TownForm(forms.ModelForm):
    class Meta:
        model = Town
        fields = ['province', 'name', 'latitude', 'longitude']