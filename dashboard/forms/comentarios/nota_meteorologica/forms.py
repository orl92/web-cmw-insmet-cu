from django import forms
from dashboard.models import WeatherNote

class WeatherNoteForm(forms.ModelForm):
    class Meta:
        model = WeatherNote
        fields = ['subject', 'detailed_note']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance
