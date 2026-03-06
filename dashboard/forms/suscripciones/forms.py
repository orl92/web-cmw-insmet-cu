from django import forms

from dashboard.models import Certificate, Service, ServiceSubscription


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = ServiceSubscription
        fields = ['customer', 'service', 'start_date', 'end_date', 'payment_status']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'service': forms.Select(attrs={'class': 'form-control'}),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar servicios: solo comerciales
        self.fields['service'].queryset = Service.objects.filter(service_type=Service.COMMERCIAL)
        # Si es edición, deshabilitar el campo payment_status (como ya tenías)
        if self.instance and self.instance.pk:
            self.fields['payment_status'].disabled = True
            self.fields['payment_status'].help_text = "El estado solo puede modificarse mediante acciones específicas (facturar, aprobar, regenerar)."


class CertificateUploadForm(forms.ModelForm):
    """Formulario para subir el certificado (basado en modelo Certificate)"""
    class Meta:
        model = Certificate
        fields = ['pdf']
        widgets = {
            'pdf': forms.FileInput(attrs={'accept': '.pdf', 'required': True, 'class': 'form-control'})
        }


class InvoiceForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Monto de la factura",
        widget=forms.NumberInput(attrs={
            'step': '0.01', 
            'min': '0', 
            'class': 'form-control',
            'placeholder': '0.00'
        })
    )
    
    start_date = forms.DateField(
        label="Fecha de inicio",
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control'
        })
    )
    
    end_date = forms.DateField(
        label="Fecha de expiración",
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control'
        })
    )

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("El monto debe ser mayor que cero.")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        
        if start and end:
            if start >= end:
                raise forms.ValidationError(
                    "La fecha de inicio debe ser anterior a la fecha de expiración."
                )
            
            # Validación opcional: no permitir períodos demasiado largos
            days_diff = (end - start).days
            if days_diff > 365:  # Máximo 1 año
                raise forms.ValidationError(
                    "El período no puede ser mayor a 365 días."
                )
        
        return cleaned_data


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
