import contextlib

from django import forms
from django.forms import formset_factory

from apps.commercial.models import Customer, Service, ServiceSubscription
from apps.core.models import CompanySettings


class InvoiceItemForm(forms.Form):
    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(service_type=Service.COMMERCIAL, record_active=True),
        required=True,
        label='Servicio',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    codigo = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
    )
    cantidad = forms.IntegerField(
        min_value=1,
        required=True,
        label='Cantidad',
        help_text='Cantidad de meses o días según el tipo de servicio.',
        widget=forms.NumberInput(attrs={'class': 'form-control quantity-days', 'min': '1'}),
    )
    unidad_medida = forms.CharField(
        max_length=5,
        initial='U',
        label='UM',
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
    )
    precio = forms.DecimalField(
        min_value=0.01,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
    )

    def clean(self):
        """Rebuild the readonly fields from the service, never from the POST body.

        `codigo`, `precio` and `unidad_medida` exist so the operator can see what
        is being charged, not so a stale page or a hand-crafted request can set
        them. `unidad_medida` follows the service category: agrometeo bills months,
        every other category bills days, so the same period means 3 for agrometeo
        and 90 for pronostico. `cantidad` is the opposite — the operator owns it,
        and the browser only proposes a value for it.
        """
        cleaned_data = super().clean()
        service = cleaned_data.get('service')

        if service:
            cleaned_data['codigo'] = service.code or ''
            cleaned_data['precio'] = service.price
            cleaned_data['unidad_medida'] = (
                'MES' if service.service_category == 'agrometeo' else 'DÍA'
            )

        return cleaned_data


InvoiceItemFormSet = formset_factory(InvoiceItemForm, extra=1, can_delete=True)


class InvoiceForm(forms.Form):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(record_active=True),
        label='Cliente',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_customer'}),
    )
    start_date = forms.DateField(
        label='Fecha de inicio',
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    end_date = forms.DateField(
        label='Fecha de fin',
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    commercial_registry = forms.CharField(
        max_length=50,
        required=True,
        label='Registro Comercial',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    subscriptions = forms.ModelMultipleChoiceField(
        queryset=ServiceSubscription.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Suscripciones a facturar',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        company = CompanySettings.get_instance()
        self.fields['commercial_registry'].initial = company.registro_comercial

        customer_id = None
        if 'customer' in self.data:
            with contextlib.suppress(ValueError, TypeError):
                customer_id = int(self.data.get('customer'))
        elif self.initial and self.initial.get('customer'):
            customer = self.initial['customer']
            customer_id = customer.pk if hasattr(customer, 'pk') else customer

        if customer_id:
            self.fields['subscriptions'].queryset = ServiceSubscription.objects.filter(
                customer_id=customer_id,
                payment_status__in=['requested', 'pending'],
                record_active=True,
            )
        else:
            self.fields['subscriptions'].queryset = ServiceSubscription.objects.none()
