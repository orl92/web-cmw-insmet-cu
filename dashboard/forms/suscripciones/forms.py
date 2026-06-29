from datetime import timedelta

from django import forms
from django.utils import timezone

from dashboard.models import Certificate, Service, ServiceSubscription


class SubscriptionForm(forms.ModelForm):
    PERIOD_CHOICES = [
        ('1m', '1 mes'),
        ('3m', '3 meses'),
        ('6m', '6 meses'),
        ('1y', '1 año'),
        ('custom', 'Personalizado (elegir fechas)'),
    ]
    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        label="Período",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_period'}),
        required=False,
    )

    class Meta:
        model = ServiceSubscription
        fields = ['customer', 'service', 'start_date', 'end_date', 'payment_status', 'period']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'id': 'id_start_date'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'id': 'id_end_date'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'service': forms.Select(attrs={'class': 'form-control'}),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].queryset = Service.objects.filter(service_type=Service.COMMERCIAL)
        if self.instance and self.instance.pk:
            self.fields['payment_status'].disabled = True
            self.fields['payment_status'].help_text = "El estado solo puede modificarse mediante acciones específicas."
            # Si ya tiene fechas, intentamos deducir el período seleccionado
            if self.instance.start_date and self.instance.end_date:
                delta = (self.instance.end_date - self.instance.start_date).days
                if 28 <= delta <= 31:
                    self.initial['period'] = '1m'
                elif 85 <= delta <= 92:
                    self.initial['period'] = '3m'
                elif 175 <= delta <= 185:
                    self.initial['period'] = '6m'
                elif 360 <= delta <= 370:
                    self.initial['period'] = '1y'
                else:
                    self.initial['period'] = 'custom'
        else:
            self.initial['period'] = '1m'  # valor por defecto

    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')

        if period != 'custom':
            # Si se elige un período predefinido, forzar fechas adecuadas
            today = timezone.now()
            if not start:
                start = today
                cleaned_data['start_date'] = start
            if period == '1m':
                end = start + timedelta(days=30)
            elif period == '3m':
                end = start + timedelta(days=90)
            elif period == '6m':
                end = start + timedelta(days=180)
            elif period == '1y':
                end = start + timedelta(days=365)
            cleaned_data['end_date'] = end
        else:
            # Validar que las fechas sean coherentes
            if start and end and start >= end:
                raise forms.ValidationError("La fecha de inicio debe ser anterior a la de fin.")
        return cleaned_data


class CertificateUploadForm(forms.ModelForm):
    """Formulario para subir el certificado (basado en modelo Certificate)"""
    class Meta:
        model = Certificate
        fields = ['pdf']
        widgets = {
            'pdf': forms.FileInput(attrs={'accept': '.pdf', 'required': True, 'class': 'form-control'})
        }


class InvoiceForm(forms.Form):
    start_date = forms.DateField(
        label="Fecha de inicio",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        label="Fecha de expiración",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    commercial_registry = forms.CharField(
        max_length=50,
        required=True,
        label="Registro Comercial",
        help_text="Ej: A09404",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'A09404'})
    )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end:
            if start >= end:
                raise forms.ValidationError("La fecha de inicio debe ser anterior a la fecha de expiración.")
            if (end - start).days > 365:
                raise forms.ValidationError("El período no puede ser mayor a 365 días.")
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
