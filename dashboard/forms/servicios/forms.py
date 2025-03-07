from django import forms

from dashboard.models import Service


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['title', 'summary', 'service_type', 'target_customer', 'file']

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

