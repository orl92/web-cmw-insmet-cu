from django import forms
from dashboard.models import CompanySettings

class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        fields = [
            'nombre', 'direccion', 'codigo_reeup', 'nit',
            'cuenta_bancaria', 'agencia_bancaria', 'telefonos', 'registro_comercial'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_reeup': forms.TextInput(attrs={'class': 'form-control'}),
            'nit': forms.TextInput(attrs={'class': 'form-control'}),
            'cuenta_bancaria': forms.TextInput(attrs={'class': 'form-control'}),
            'agencia_bancaria': forms.TextInput(attrs={'class': 'form-control'}),
            'telefonos': forms.TextInput(attrs={'class': 'form-control'}),
            'registro_comercial': forms.TextInput(attrs={'class': 'form-control'}),
        }
