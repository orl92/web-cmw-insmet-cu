from django import forms
from django.utils import timezone

from apps.commercial.models import Contract, Customer


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ['customer', 'number', 'start_date', 'validity_years']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2025-0001'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'validity_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.filter(record_active=True)
        if not self.instance.pk:
            self.fields['start_date'].initial = timezone.localdate()
            self.fields['validity_years'].initial = 2
