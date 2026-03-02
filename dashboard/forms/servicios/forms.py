from dashboard.models import Service
from django import forms


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['title', 'summary', 'service_type', 'pdf', 'image']
        widgets = {
            'pdf': forms.FileInput(attrs={'accept': '.pdf'}),
            'image': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Eliminamos la lógica de required del __init__

    def clean(self):
        cleaned_data = super().clean()
        service_type = cleaned_data.get('service_type')
        pdf = cleaned_data.get('pdf')
        image = cleaned_data.get('image')

        # Archivos existentes (si es edición)
        existing_pdf = self.instance.pdf if self.instance.pk else None
        existing_image = self.instance.image if self.instance.pk else None

        if service_type == Service.PUBLIC:
            # Debe haber PDF (nuevo o existente)
            if not pdf and not existing_pdf:
                self.add_error('pdf', 'Para servicios públicos es obligatorio un archivo PDF.')
            if image:
                self.add_error('image', 'Los servicios públicos no deben tener imagen.')
        elif service_type == Service.COMMERCIAL:
            # Debe haber imagen (nueva o existente)
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
