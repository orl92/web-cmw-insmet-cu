from django import forms

from apps.dashboard.models import TropicalCyclone


class TropicalCycloneForm(forms.ModelForm):
    class Meta:
        model = TropicalCyclone
        fields = ['summary', 'valid_until', 'file', 'email_recipient_list']
        widgets = {
            'email_recipient_list': forms.Select(attrs={'class': 'form-select'}),
        }

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