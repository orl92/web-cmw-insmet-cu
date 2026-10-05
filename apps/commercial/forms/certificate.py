from django import forms

from apps.commercial.models import Certificate, ServiceSubscription


class CertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = ['subscription', 'pdf']
        widgets = {
            'subscription': forms.Select(attrs={'class': 'form-control'}),
            'pdf': forms.FileInput(attrs={'accept': '.pdf', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # `customer__user` porque el `<option>` y la etiqueta arman el nombre con
        # `display_name`, que cae en el User del natural: sin el join, un N+1
        # por cada suscripción elegible.
        self.fields['subscription'].queryset = ServiceSubscription.objects.filter(
            record_active=True
        ).select_related('customer__user', 'service')
        self.fields['subscription'].label_from_instance = lambda obj: (
            f'{obj.customer.display_name} - {obj.service.title}'
        )
