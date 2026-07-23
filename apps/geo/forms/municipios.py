from django import forms

from apps.geo.models import Town


class TownForm(forms.ModelForm):
    class Meta:
        model = Town
        fields = ['province', 'name', 'latitude', 'longitude']
