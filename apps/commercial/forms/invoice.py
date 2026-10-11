import calendar
import contextlib
from datetime import date
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.forms import formset_factory, modelformset_factory
from django.forms.models import BaseModelFormSet
from django.utils import timezone

from apps.commercial.forms.subscription import _pluralize_period
from apps.commercial.models import (
    MESES,
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


def meses_del_periodo():
    return [(str(numero), nombre.capitalize()) for numero, nombre in enumerate(MESES, start=1)]


def anios_del_periodo(hoy):
    """Años ofrecidos, de dos años antes de hoy hasta el año siguiente.

    Hacia atrás porque el período va atrasado con frecuencia real: la
    certificación agrometeorológica que el cliente no pudo cumplir a tiempo se
    factura igual, y es el caso que justifica que el período pueda ser del pasado.
    """
    return [(str(anio), str(anio)) for anio in range(hoy.year - 2, hoy.year + 2)]


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
    month_from = forms.ChoiceField(
        choices=(),
        label='Mes desde',
        required=False,
    )
    year = forms.ChoiceField(
        choices=(),
        label='Año',
        required=False,
    )
    month_to = forms.ChoiceField(
        choices=(),
        label='Mes hasta',
        required=False,
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
        hoy = timezone.localdate()
        meses = meses_del_periodo()
        anios = anios_del_periodo(hoy)
        for nombre in ('month_from', 'month_to'):
            self.fields[nombre].choices = [('', '---------')] + meses
            self.fields[nombre].widget.attrs.update({'class': 'form-select'})
        self.fields['year'].choices = [('', '---------')] + anios
        self.fields['year'].widget.attrs.update({'class': 'form-select'})
        self.fields['year'].initial = str(hoy.year)

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

    def clean(self):
        cleaned_data = super().clean()
        # En lote el período NO se pide: lo deduce cada suscripción de su fecha de
        # inicio y la vista lo descarta. Sólo la facturación manual necesita el rango.
        if cleaned_data.get('subscriptions'):
            return cleaned_data

        anio = cleaned_data.get('year')
        mes_desde = cleaned_data.get('month_from')
        mes_hasta = cleaned_data.get('month_to')
        if not anio or not mes_desde or not mes_hasta:
            raise ValidationError('Elegí el año, el mes desde y el mes hasta del período.')

        start = date(int(anio), int(mes_desde), 1)
        end = date(int(anio), int(mes_hasta), calendar.monthrange(int(anio), int(mes_hasta))[1])
        if start > end:
            raise ValidationError('El mes de inicio no puede ser posterior al mes de fin.')

        cleaned_data['period_start'] = start
        cleaned_data['period_end'] = end
        return cleaned_data
