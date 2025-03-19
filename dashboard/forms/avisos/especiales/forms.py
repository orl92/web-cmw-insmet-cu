from django import forms
from dashboard.models import SpecialNotice 

class SpecialNoticeForm(forms.ModelForm):
    class Meta:
        model = SpecialNotice
        fields = ['title', 'subject', 'valid_until', 'image', 'description', 'email_recipient_list']
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