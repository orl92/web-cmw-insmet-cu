from django import forms
from apps.commercial.models import Service


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['title', 'summary', 'service_type', 'pdf', 'image', 'code', 'price']
        widgets = {
            'pdf': forms.FileInput(attrs={'accept': '.pdf'}),
            'image': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['code'].required = False
        self.fields['price'].required = False

    def clean(self):
        cleaned_data = super().clean()
        service_type = cleaned_data.get('service_type')
        pdf = cleaned_data.get('pdf')
        image = cleaned_data.get('image')
        code = cleaned_data.get('code')
        price = cleaned_data.get('price')

        existing_pdf = self.instance.pdf if self.instance.pk else None
        existing_image = self.instance.image if self.instance.pk else None

        if service_type == Service.PUBLIC:
            cleaned_data['code'] = None
            cleaned_data['price'] = None
            if not pdf and not existing_pdf:
                self.add_error('pdf', 'Para servicios públicos es obligatorio un archivo PDF.')
            if image:
                self.add_error('image', 'Los servicios públicos no deben tener imagen.')
        elif service_type == Service.COMMERCIAL:
            if not code:
                self.add_error('code', 'El código del servicio es obligatorio para servicios comerciales.')
            if price is None:
                self.add_error('price', 'El precio es obligatorio para servicios comerciales.')
            if not image and not existing_image:
                self.add_error('image', 'Para servicios comerciales es obligatorio una imagen.')
            if pdf:
                self.add_error('pdf', 'Los servicios comerciales no deben tener PDF adjunto.')
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance
