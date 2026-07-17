from django import forms

from dashboard.models import Contract


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ['subscription', 'number', 'date', 'commercial_registry']
        widgets = {
            'subscription': forms.Select(attrs={'class': 'form-control'}),
            'number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2025-0001'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'commercial_registry': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'A09404'}),
        }
