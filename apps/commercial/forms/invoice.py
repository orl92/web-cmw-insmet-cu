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

    El rótulo de `cantidad` nombra la unidad porque es el único lugar donde el
    operador puede leerla: la columna `U/M` de las facturas del CMP dice `U` o
    nada. Se resuelve en el servidor para que una fila que vuelve a renderizarse
    por un error llegue rotulada sin JavaScript.

    `cantidad` no trae valor por defecto: las cantidades reales son 30, 31, 2 y
    4, y un número inventado acá subfactura en silencio.
    """

    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(service_type=Service.COMMERCIAL, record_active=True),
        required=True,
        label='Servicio',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    start_date = forms.DateField(
        label='Inicio',
        # Sin `help_text` a propósito: la regla ("viene con la fecha de la
        # factura; cambiala sólo si el servicio empezó antes") se explica una
        # sola vez en el encabezado de la card de servicios. Repetida en cada
        # línea ocupaba medio campo por servicio y partía el card en dos filas
        # de controles.
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
    # `unidad_medida` no es un campo, y es deliberado. Las tres facturas reales
    # del CMP la impresión casi siempre vacía y a veces como `U`, con cantidades
    # de 30, 31, 2 y 4: ninguna dice `MES` ni `DÍA`. La unidad de la fila la
    # nombra el rótulo de `cantidad`, así que `U/M` no aporta nada que leer y su
    # valor tiene un solo dueño, el `default='U'` de `InvoiceItem`. Un campo
    # `readonly` acá sólo repetiría esa constante en la pantalla y obligaría a
    # mantener el código que lo reescribía —el que inventaba `MES`/`DÍA`—, que
    # es justo lo que esta tarea vino a borrar. Sin campo, el POST tampoco tiene
    # el nombre para intentar fijarlo.
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

        Va acá y no en `clean()` porque el rótulo se imprime antes de validar:
        una fila que vuelve por un error tiene que llegar rotulada. `add_prefix`
        porque la misma clase se usa suelta y dentro del formset.
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
        # `codigo` y `precio` se reconstruyen desde el servicio y nunca desde el
        # POST: existen para que el operador vea qué se está cobrando, no para que
        # una página vieja o un POST a mano los fijen.
        cleaned_data = super().clean()
        service = cleaned_data.get('service')

        if service:
            cleaned_data['codigo'] = service.code or ''
            cleaned_data['precio'] = service.price

        return cleaned_data


InvoiceItemFormSet = formset_factory(InvoiceItemForm, extra=1, can_delete=True)


class InvoiceCostAllocationForm(forms.ModelForm):
    class Meta:
        model = InvoiceCostAllocation
        fields = ['codigo', 'porcentaje']
        widgets = {
            # El centro sigue siendo un `TextInput` a propósito: el `datalist`
            # sugiere pero no restringe, así que un centro que no está en el
            # catálogo se puede escribir igual. Un `Select` sí lo restringiría y
            # cerraría la puerta a los centros de las facturas reales 276 y 279,
            # que no salen de ningún código de servicio.
            'codigo': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'list': 'centros-de-costo',
                    'autocomplete': 'off',
                    'placeholder': '700.50107',
                }
            ),
            'porcentaje': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}
            ),
        }


class InvoiceCostAllocationFormSet(BaseModelFormSet):
    """Formset de centros de costo, con la regla de que sumen 100 %.

    La suma se valida acá y no en el modelo: en `clean()` no se podría borrar
    una fila y corregir el reparto, porque al guardar la primera vez ya se
    exigiría el total. Sólo se cuentan las formas vivas, así que `can_delete`
    recalcula bien.
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
# Sin `queryset=` acá: `modelformset_factory` no lo acepta. El que el formset se
# acote o no lo decide la vista al instanciarlo: un modelformset sin acotar cae
# al manager del modelo y `initial_form_count()` pasa a ser `len(get_queryset())`,
# así que la pantalla abría con TODAS las imputaciones de la base como filas
# editables, más la fila en blanco de `extra=1`. Ver
# `InvoiceCreateView.cost_allocations_formset`.


class InvoiceForm(forms.Form):
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
