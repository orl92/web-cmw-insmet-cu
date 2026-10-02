from django import forms
from django.conf import settings
from django.utils import timezone

from apps.commercial.models import Certificate, Service, ServiceSubscription
from apps.core.widgets import TempusAwareDateTimeInput


class ServicePeriodUnitSelect(forms.Select):
    """Select de servicio que publica la unidad de facturación de cada opción.

    La unidad no es elegible: sale de la categoría del servicio, así que viaja en
    la propia `<option>` y el navegador rotula la cantidad sin volver a pedírsela
    al servidor.
    """

    period_units = None

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        unit = (self.period_units or {}).get(str(value))
        if unit:
            option['attrs']['data-period-unit'] = unit
        return option


class SubscriptionForm(forms.ModelForm):
    """Alta y edición de suscripciones: fecha de inicio libre y cantidad del período.

    La unidad (días o meses) la decide la categoría del servicio, no quien crea
    la suscripción. Por eso `end_date` no es un campo del formulario sino un
    valor derivado de inicio y cantidad, y `quantity` es la magnitud que el
    operador sí fija: es lo que multiplica al precio.
    """

    start_date = forms.DateTimeField(
        # Campo declarado: sin `label` explícito Django rotula con el nombre del
        # atributo ("Start date") e ignora el verbose_name del modelo.
        label='Fecha de inicio',
        input_formats=['%d/%m/%Y %I:%M %p', '%Y-%m-%dT%H:%M', '%d/%m/%Y %H:%M'],
        widget=TempusAwareDateTimeInput(attrs={'class': 'form-control'}),
        required=True,
    )
    quantity = forms.IntegerField(
        min_value=1,
        required=True,
        label='Cantidad',
        # El texto del modelo es la fuente de la ayuda: la unidad depende de la
        # categoría del servicio y no de un campo propio del formulario.
        help_text=ServiceSubscription._meta.get_field('quantity').help_text,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
    )

    class Meta:
        model = ServiceSubscription
        fields = ['customer', 'service', 'start_date', 'quantity', 'payment_status']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'service': ServicePeriodUnitSelect(attrs={'class': 'form-control'}),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        service_field = self.fields['service']
        service_field.queryset = Service.objects.filter(service_type=Service.COMMERCIAL)
        self.fields['service'].widget.period_units = {
            str(service.pk): service.get_billing_period_display()
            for service in service_field.queryset
        }
        if self.instance and self.instance.pk:
            self.fields['payment_status'].disabled = True
            self.fields[
                'payment_status'
            ].help_text = 'El estado solo puede modificarse mediante acciones específicas.'

    @property
    def derived_end_date(self):
        """Vencimiento que el servidor calcula para lo que el formulario muestra.

        Es el valor que se imprime en la plantilla, así que el operador lo ve sin
        JavaScript; el navegador sólo lo recalcula mientras edita. Se devuelve en
        hora local porque la base la guarda en UTC y el filtro de la plantilla
        formatea el valor tal cual.
        """
        if self.is_bound:
            start = self.cleaned_data.get('start_date')
            quantity = self.cleaned_data.get('quantity')
            service = self.cleaned_data.get('service')
        else:
            start = self.instance.start_date
            quantity = self.instance.quantity
            service = self.instance.service if self.instance.pk else None
        if not (start and quantity and service):
            return None
        end = Service.compute_end_date(start, quantity, service.service_category)
        return timezone.localtime(end) if settings.USE_TZ else end

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        quantity = cleaned_data.get('quantity')
        service = cleaned_data.get('service')
        if start and quantity and service:
            # El vencimiento se escribe en la instancia y no sólo en
            # `cleaned_data` porque `end_date` ya no está en `Meta.fields`: es
            # `_post_clean` quien valida el invariante `start < end` del modelo,
            # y para eso la instancia tiene que traer el valor derivado.
            self.instance.end_date = Service.compute_end_date(
                start, quantity, service.service_category
            )
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
