from django import forms

from apps.meteo.models import Warning


class WarningForm(forms.ModelForm):
    class Meta:
        model = Warning
        fields = ['summary', 'valid_until', 'file', 'email_recipient_list']
        widgets = {
            'email_recipient_list': forms.Select(attrs={'class': 'form-select'}),
            'valid_until': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.warning_type = kwargs.pop('warning_type', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if self.warning_type:
            instance.warning_type = self.warning_type
        if commit:
            instance.save()
        return instance
