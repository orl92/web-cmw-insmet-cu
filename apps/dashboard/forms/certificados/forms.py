from django import forms

from apps.crm.models import ServiceSubscription
from apps.dashboard.models import Certificate


class CertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = ['subscription', 'pdf']
        widgets = {
            'subscription': forms.Select(attrs={'class': 'form-control'}),
            'pdf': forms.FileInput(attrs={'accept': '.pdf', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subscription'].queryset = ServiceSubscription.objects.filter(
            record_active=True
        ).select_related('customer', 'service')
        self.fields['subscription'].label_from_instance = (
            lambda obj: f"{obj.customer.company_name} - {obj.service.title}"
        )
