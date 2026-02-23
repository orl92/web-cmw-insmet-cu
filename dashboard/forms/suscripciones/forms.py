from django import forms
from dashboard.models import ServiceSubscription

class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = ServiceSubscription
        fields = ['customer', 'service', 'start_date', 'end_date', 'payment_status']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class CertificateUploadForm(forms.ModelForm):
    class Meta:
        model = ServiceSubscription
        fields = ['certificate']
        widgets = {
            'certificate': forms.FileInput(attrs={'accept': '.pdf', 'required': True})
        }
