from django import forms

from apps.dashboard.models import WeatherReport


class WeatherReportForm(forms.ModelForm):
    class Meta:
        model = WeatherReport
        fields = ['summary', 'file', 'email_recipient_list']
        widgets = {
            'email_recipient_list': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.report_type = kwargs.pop('report_type', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if self.report_type:
            instance.report_type = self.report_type
        if commit:
            instance.save()
        return instance
