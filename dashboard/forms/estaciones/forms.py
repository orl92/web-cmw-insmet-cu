from django import forms

from dashboard.models import Station


class StationForm(forms.ModelForm):
    class Meta:
        model = Station
        fields = ['province', 'name', 'number', 'latitude', 'longitude']