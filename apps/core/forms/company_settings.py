from django import forms

from apps.core.models import CompanySettings
from apps.core.validators import validate_account, validate_nit, validate_phones, validate_reeup


class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        fields = [
            'nombre',
            'direccion',
            'codigo_reeup',
            'nit',
            'cuenta_bancaria',
            'agencia_bancaria',
            'telefonos',
            'registro_comercial',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_reeup': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '123.1.1234',
                    'maxlength': '12',
                    'pattern': r'\d{3}\.\d{1,2}\.\d{4,5}',
                    'inputmode': 'numeric',
                }
            ),
            'nit': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '12345678901',
                    'maxlength': '11',
                    'pattern': r'\d{11}',
                    'inputmode': 'numeric',
                }
            ),
            'cuenta_bancaria': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '1234567890123456',
                    'maxlength': '16',
                    'pattern': r'\d{16}',
                    'inputmode': 'numeric',
                }
            ),
            'agencia_bancaria': forms.TextInput(attrs={'class': 'form-control'}),
            'telefonos': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '51234567, 32270000',
                    'maxlength': '100',
                    'pattern': r'\d{8}([\s,\-;]+\d{8})*',
                    'inputmode': 'numeric',
                }
            ),
            'registro_comercial': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_codigo_reeup(self):
        return validate_reeup(self.cleaned_data.get('codigo_reeup'))

    def clean_nit(self):
        return validate_nit(self.cleaned_data.get('nit'))

    def clean_cuenta_bancaria(self):
        return validate_account(self.cleaned_data.get('cuenta_bancaria'))

    def clean_telefonos(self):
        return validate_phones(self.cleaned_data.get('telefonos'))
