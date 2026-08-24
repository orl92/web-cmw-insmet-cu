from datetime import timedelta

from django import forms
from django.utils import timezone

from apps.commercial.models import Certificate, Service, ServiceSubscription


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
        label='Período',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_period'}),
        required=False,
    )

    start_date = forms.DateTimeField(
        input_formats=['%d/%m/%Y %I:%M %p', '%Y-%m-%dT%H:%M', '%d/%m/%Y %H:%M'],
        widget=forms.DateTimeInput(attrs={'class': 'form-control'}),
        required=False,
    )
    end_date = forms.DateTimeField(
        input_formats=['%d/%m/%Y %I:%M %p', '%Y-%m-%dT%H:%M', '%d/%m/%Y %H:%M'],
        widget=forms.DateTimeInput(attrs={'class': 'form-control'}),
        required=False,
    )

    class Meta:
        model = ServiceSubscription
        fields = ['customer', 'service', 'start_date', 'end_date', 'payment_status', 'period']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'service': forms.Select(attrs={'class': 'form-control'}),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].queryset = Service.objects.filter(service_type=Service.COMMERCIAL)
        if self.instance and self.instance.pk:
            self.fields['payment_status'].disabled = True
            self.fields[
                'payment_status'
            ].help_text = 'El estado solo puede modificarse mediante acciones específicas.'
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
            self.initial['period'] = '1m'

    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')

        if period != 'custom':
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
            if start and end and start >= end:
                raise forms.ValidationError('La fecha de inicio debe ser anterior a la de fin.')
        return cleaned_data


class CertificateUploadForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = ['pdf']
        widgets = {
            'pdf': forms.FileInput(
                attrs={'accept': '.pdf', 'required': True, 'class': 'form-control'}
            )
        }


class PaymentMethodForm(forms.Form):
    PAYMENT_METHOD_CHOICES = [
        ('qr', 'Pago por Código QR'),
        ('transfer', 'Transferencia Bancaria'),
        ('presencial', 'Pago Presencial'),
    ]
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES, widget=forms.RadioSelect, label='Método de pago'
    )
    start_date = forms.DateField(
        label='Fecha de inicio del servicio',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True,
        help_text='Fecha desde la cual necesita el servicio.',
    )
    end_date = forms.DateField(
        label='Fecha de fin del servicio',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True,
        help_text='Fecha hasta la cual necesita el servicio.',
    )


class InvoiceForm(forms.Form):
    PAYMENT_METHOD_CHOICES = [
        ('qr', 'Pago por Código QR'),
        ('transfer', 'Transferencia Bancaria'),
        ('presencial', 'Pago Presencial'),
    ]
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES, widget=forms.RadioSelect, label='Método de pago'
    )
    start_date = forms.DateField(
        label='Fecha de inicio del servicio',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True,
        help_text='Fecha desde la cual necesita el servicio.',
    )
    end_date = forms.DateField(
        label='Fecha de fin del servicio',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True,
        help_text='Fecha hasta la cual necesita el servicio.',
    )
