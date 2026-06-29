from django import forms
from django.forms import formset_factory
from dashboard.models import Customer, Service, ServiceSubscription, CompanySettings

class InvoiceItemForm(forms.Form):
    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(service_type=Service.COMMERCIAL),
        required=True,                  # <-- Obligatorio, sin opción vacía
        label="Servicio",
        widget=forms.Select(attrs={'class': 'form-control'})
        # no se define empty_label, así que no aparece "-- Otro (manual) --"
    )
    codigo = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))
    cantidad = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    unidad_medida = forms.CharField(max_length=5, initial='U', label='UM', widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))
    precio = forms.DecimalField(min_value=0.01, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))

InvoiceItemFormSet = formset_factory(InvoiceItemForm, extra=1, can_delete=True)

class InvoiceForm(forms.Form):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
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
        if 'customer' in self.data:
            try:
                customer_id = int(self.data.get('customer'))
                self.fields['subscriptions'].queryset = ServiceSubscription.objects.filter(
                    customer_id=customer_id,
                    payment_status__in=['requested', 'pending'],
                    record_active=True,
                )
            except (ValueError, TypeError):
                pass
