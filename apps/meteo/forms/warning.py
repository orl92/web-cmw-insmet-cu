from django import forms

from apps.meteo.models import Warning


class WarningForm(forms.ModelForm):
    valid_until = forms.DateTimeField(
        input_formats=['%d/%m/%Y %I:%M %p', '%Y-%m-%dT%H:%M', '%d/%m/%Y %H:%M'],
        widget=forms.DateTimeInput(attrs={'class': 'form-control'}),
        label='Válido hasta',
    )

    class Meta:
        model = Warning
        fields = ['summary', 'valid_until', 'file', 'email_recipient_list']
        widgets = {
            'email_recipient_list': forms.Select(attrs={'class': 'form-select'}),
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
