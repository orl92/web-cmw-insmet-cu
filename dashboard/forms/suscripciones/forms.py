from dashboard.models import Certificate, ServiceSubscription
from django import forms


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = ServiceSubscription
        fields = ['customer', 'service', 'start_date', 'end_date', 'payment_status']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class CertificateUploadForm(forms.ModelForm):
    """Formulario para subir el certificado (basado en modelo Certificate)"""
    class Meta:
        model = Certificate
        fields = ['pdf']
        widgets = {
            'pdf': forms.FileInput(attrs={'accept': '.pdf', 'required': True, 'class': 'form-control'})
        }


class InvoiceAmountForm(forms.Form):
    """Formulario para que el staff ingrese el monto de la factura"""
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Monto de la factura",
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control'})
    )

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("El monto debe ser mayor que cero.")
        return amount


class PaymentMethodForm(forms.Form):
    PAYMENT_METHOD_CHOICES = [
        ('qr', 'Pago por Código QR'),
        ('transfer', 'Transferencia Bancaria'),
        ('presencial', 'Pago Presencial'),
    ]

    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Método de pago"
    )
