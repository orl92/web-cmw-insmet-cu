import contextlib
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.forms import formset_factory, modelformset_factory
from django.forms.models import BaseModelFormSet

from apps.commercial.forms.subscription import _pluralize_period
from apps.commercial.models import (
    Customer,
    InvoiceCostAllocation,
    Service,
    ServiceSubscription,
)
from apps.core.models import CompanySettings


class InvoiceItemForm(forms.Form):
    """Una línea de facturación manual.

    El rótulo de `cantidad` nombra la unidad —"Cantidad de meses" o "Cantidad de
    días"— porque es el único lugar donde el operador puede leerla: la columna
    `U/M` de las facturas reales del CMP nunca dice `MES` ni `DÍA`, dice `U` o
    nada. La unidad no es un dato propio, sale de la categoría del servicio, y
    se resuelve en el servidor para que una fila que vuelve a renderizarse por
    un error se rotule igual sin que haya corrido una línea de JavaScript.

    `cantidad` no trae valor por defecto. Las cantidades reales son 30, 31, 2 y
    4, nunca 1: un número inventado en este campo subfactura en silencio.
    """

    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(service_type=Service.COMMERCIAL, record_active=True),
        required=True,
        label='Servicio',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    start_date = forms.DateField(
        label='Inicio del servicio',
        help_text=(
            'Fecha en que el servicio empieza para el cliente. Ya viene con la '
            'fecha de la factura: cambiala sólo si el servicio empezó antes.'
        ),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    codigo = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
    )
    # Sin `initial` y sin `default` a propósito: la cantidad la cuenta quien
    # factura, y un valor propuesto que no revisa cobra de menos.
    cantidad = forms.IntegerField(
        min_value=1,
        required=True,
        label='Cantidad',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        unidad = self._selected_billing_period()
        if unidad:
            self.fields['cantidad'].label = f'Cantidad de {_pluralize_period(unidad)}'

    def _selected_billing_period(self):
        """Unidad de facturación del servicio ya elegido, o `''` si no hay ninguno.

        Se resuelve acá y no en el `clean()` porque el rótulo se imprime antes de
        validar: una fila que vuelve a la pantalla por un error tiene que llegar
        rotulada, y en ese momento el POST todavía no es válido. Igual que en
        `SubscriptionForm`, sólo un servicio del queryset cuenta: uno
        inexistente, uno público o uno dado de baja dejan el rótulo neutro en vez
        de romper el render.

        `add_prefix` porque la misma clase se usa suelta y dentro del formset,
        donde los datos llegan como `items-0-service` y no como `service`.
        """
        if not self.is_bound:
            return ''
        elegido = self.data.get(self.add_prefix('service'))
        if not elegido:
            return ''
        try:
            servicio = self.fields['service'].clean(elegido)
        except ValidationError:
            return ''
        return servicio.get_billing_period_display() if servicio else ''

    def clean(self):
        """Rebuild the readonly fields from the service, never from the POST body.

        `codigo`, `precio` and `unidad_medida` exist so the operator can see what
        is being charged, not so a stale page or a hand-crafted request can set
        them. `unidad_medida` follows the service category: agrometeo bills months,
        every other category bills days, so the same period means 3 for agrometeo
        and 90 for pronostico. `cantidad` is the opposite — the operator owns it,
        and `start_date` is its own too: it is the contract with the customer, so
        it travels per line and is never derived from the invoice.

        There is no unit selector on purpose: it would duplicate a fact that
        `service_category` already states.
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


class InvoiceCostAllocationForm(forms.ModelForm):
    class Meta:
        model = InvoiceCostAllocation
        fields = ['codigo', 'porcentaje']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'porcentaje': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}
            ),
        }


class InvoiceCostAllocationFormSet(BaseModelFormSet):
    """Formset de centros de costo, con la regla de que sumen 100 %.

    La suma se valida acá y no en `InvoiceCostAllocation.clean()` a propósito: en
    el modelo no se podría borrar una fila y corregir el reparto, porque al
    guardar la primera vez ya se exigiría el total. Sólo se cuentan las formas
    vivas, así que `can_delete` recalcula bien.

    Exige además al menos una fila viva: las tres facturas reales del CMP
    imputan a algún centro, y una factura comercial sin imputación es
    exactamente el defecto que este modelo viene a cerrar.
    """

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        total = Decimal('0')
        vivas = 0
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            if form.cleaned_data.get('DELETE'):
                continue
            porcentaje = form.cleaned_data.get('porcentaje')
            if porcentaje is None:
                continue
            total += porcentaje
            vivas += 1

        if vivas == 0:
            raise ValidationError('La factura debe imputarse al menos a un centro de costo.')
        if total != Decimal('100.00'):
            raise ValidationError(
                'El reparto entre centros de costo debe sumar 100 %. Suma actual: '
                f'{total.normalize()}.'
            )


InvoiceCostAllocationFormSet = modelformset_factory(
    InvoiceCostAllocation,
    form=InvoiceCostAllocationForm,
    formset=InvoiceCostAllocationFormSet,
    extra=1,
    can_delete=True,
)


class InvoiceForm(forms.Form):
    """Datos de la factura. Los períodos no están acá.

    El período facturado es `period_label` y nada más: es el texto que se
    imprime. El período del contrato (`ServiceSubscription.start_date` +
    `quantity`) es de otra entidad y viaja en cada línea de la facturación
    manual —`InvoiceItemForm.start_date`—, porque una sola fecha compartida
    obligaría a mentir en cuanto el cliente empezó dos servicios en días
    distintos.
    """

    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(record_active=True),
        label='Cliente',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_customer'}),
    )
    commercial_registry = forms.CharField(
        max_length=50,
        required=True,
        label='Registro Comercial',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    period_label = forms.CharField(
        max_length=255,
        required=False,
        label='Período facturado',
        help_text=(
            'Texto libre, tal como se imprime en la factura. Ej.: '
            '"Mes de mayo y junio de 2025". Si se deja vacío se usa la fecha de emisión.'
        ),
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Mes de mayo y junio de 2025'}
        ),
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
