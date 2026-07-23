from django import forms
from django.forms import formset_factory
from apps.crm.models import Customer, Service, ServiceSubscription
from apps.dashboard.models import CompanySettings


class InvoiceItemForm(forms.Form):
    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(service_type=Service.COMMERCIAL, record_active=True),
        required=True,
        label="Servicio",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    codigo = forms.CharField(
        max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    cantidad = forms.IntegerField(
        min_value=1, required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    unidad_medida = forms.CharField(
        max_length=5, initial='U', label='UM',
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    precio = forms.DecimalField(
        min_value=0.01, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )


InvoiceItemFormSet = formset_factory(InvoiceItemForm, extra=1, can_delete=True)


class InvoiceForm(forms.Form):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(record_active=True),
        label="Cliente",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_customer'})
    )
    start_date = forms.DateField(
        label="Fecha de inicio",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        label="Fecha de fin",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    commercial_registry = forms.CharField(
        max_length=50,
        required=True,
        label="Registro Comercial",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    subscriptions = forms.ModelMultipleChoiceField(
        queryset=ServiceSubscription.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Suscripciones a facturar"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        company = CompanySettings.get_instance()
        self.fields['commercial_registry'].initial = company.registro_comercial

        # Obtener cliente desde datos POST o valor inicial
        customer_id = None
        if 'customer' in self.data:
            try:
                customer_id = int(self.data.get('customer'))
            except (ValueError, TypeError):
                pass
        elif self.initial and self.initial.get('customer'):
            customer = self.initial['customer']
            if hasattr(customer, 'pk'):
                customer_id = customer.pk
            else:
                customer_id = customer

        if customer_id:
            self.fields['subscriptions'].queryset = ServiceSubscription.objects.filter(
                customer_id=customer_id,
                payment_status__in=['requested', 'pending'],
                record_active=True,
            )
        else:
            self.fields['subscriptions'].queryset = ServiceSubscription.objects.none()
