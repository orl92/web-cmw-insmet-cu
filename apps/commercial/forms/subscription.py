from django import forms
from django.core.exceptions import ValidationError

from apps.commercial.models import Certificate, Service, ServiceSubscription


class ServicePeriodUnitSelect(forms.Select):
    """Select de servicio que publica la unidad de facturación de cada opción.

    La unidad no es elegible: sale de la categoría del servicio, así que viaja en
    la propia `<option>` y el navegador rotula la cantidad sin volver a pedírsela
    al servidor.

    Además agrupa por categoría con `<optgroup>`. La categoría es lo único que
    determina la unidad, así que grouping por ella deja la lista ya filtrada de
    entrada sin necesidad de un select de categoría ni de JavaScript que vuelva a
    pedir la lista al servidor.
    """

    period_units = None
    categories = None

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        unit = (self.period_units or {}).get(str(value))
        if unit:
            option['attrs']['data-period-unit'] = unit
        return option

    def optgroups(self, name, value, attrs=None):
        groups = super().optgroups(name, value, attrs)
        if not self.categories:
            return groups

        labels = dict(Service.SERVICE_CATEGORY_CHOICES)
        regrouped = {}
        for _group_name, options, _index in groups:
            for option in options:
                category = self.categories.get(str(option['value']))
                key = labels.get(category, category) if category else ''
                regrouped.setdefault(key, []).append(option)
        return [(key, options, index) for index, (key, options) in enumerate(regrouped.items())]


class SubscriptionForm(forms.ModelForm):
    """Alta y edición de suscripciones: sólo se declara lo que el operador elige.

    La unidad (días o meses) la decide la categoría del servicio, no quien crea
    la suscripción. La suscripción no vence por tiempo, así que no hay ningún
    campo de expiración: `quantity` es la cantidad a facturar y multiplica al
    precio, y `payment_method` se elige al solicitar.
    """

    start_date = forms.DateField(
        label='Fecha de inicio del servicio',
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'data-tempus': 'date',
                'autocomplete': 'off',
            }
        ),
        required=True,
        help_text='Fecha desde la cual necesita el servicio.',
    )
    quantity = forms.IntegerField(
        min_value=1,
        required=True,
        label='Cantidad',
        # El texto del modelo es la fuente de los dos valores, y el form le añade
        # de dónde sale la unidad: es lo único que la comunica cuando todavía no
        # hay servicio elegido y el rótulo no puede nombrarla.
        help_text=(
            'El importe total se calcula multiplicando el precio por la cantidad seleccionada.'
        ),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
    )
    payment_method = forms.ChoiceField(
        choices=ServiceSubscription.PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect,
        label='Método de pago',
        required=True,
    )

    class Meta:
        model = ServiceSubscription
        fields = ['customer', 'service', 'start_date', 'quantity', 'payment_method']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'service': ServicePeriodUnitSelect(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        service_field = self.fields['service']
        service_field.queryset = Service.objects.filter(service_type=Service.COMMERCIAL)
        self.fields['service'].widget.period_units = {
            str(service.pk): service.get_billing_period_display()
            for service in service_field.queryset
        }
        self.fields['service'].widget.categories = {
            str(service.pk): service.service_category for service in service_field.queryset
        }
        unidad = self._selected_billing_period()
        if unidad:
            self.fields['quantity'].label = f'Cantidad de {_pluralize_period(unidad)}'

    def _selected_billing_period(self):
        """Unidad de facturación del servicio ya elegido, o `''` si no hay ninguno.

        El rótulo se imprime en el servidor para que sin JavaScript la cantidad
        siga diciendo qué se está contando. Sólo un servicio del queryset cuenta:
        uno inexistente, uno público o un POST mal formado dejan el rótulo neutro
        en vez de romper el render.
        """
        elegido = self.data.get('service') if self.is_bound else self.instance.service_id
        if not elegido:
            return ''
        try:
            servicio = self.fields['service'].clean(elegido)
        except ValidationError:
            return ''
        return servicio.get_billing_period_display() if servicio else ''


class CertificateUploadForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = ['pdf']
        widgets = {
            'pdf': forms.FileInput(
                attrs={'accept': '.pdf', 'required': True, 'class': 'form-control'}
            )
        }


def _pluralize_period(period):
    """Pluraliza un período de facturación en español ('día' -> 'días', 'mes' -> 'meses')."""
    if period.endswith(('s', 'x')):
        return f'{period}es'
    if period and period[-1] in 'aeiouáéíóú':
        return f'{period}s'
    return f'{period}es'


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
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        label='Fecha de inicio del servicio',
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'data-tempus': 'date',
                'autocomplete': 'off',
            }
        ),
        required=True,
        help_text='Fecha desde la cual necesita el servicio.',
    )
    quantity = forms.IntegerField(
        min_value=1,
        label='Cantidad',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        help_text=(
            'El importe total se calcula multiplicando el precio por la cantidad seleccionada.'
        ),
    )

    def __init__(self, *args, billing_period='día', **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quantity'].label = f'Cantidad de {_pluralize_period(billing_period)}'


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
