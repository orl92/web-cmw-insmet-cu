from django import forms

from apps.dashboard.models import Town


class TownForm(forms.ModelForm):
    class Meta:
        model = Town
        fields = ['province', 'name', 'latitude', 'longitude']