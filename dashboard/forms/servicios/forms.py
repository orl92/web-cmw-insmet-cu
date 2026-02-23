from dashboard.models import Service
from django import forms


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['title', 'summary', 'service_type', 'file']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Si es edición y el servicio es comercial, el archivo no es requerido
        if self.instance.pk and self.instance.service_type == Service.COMMERCIAL:
            self.fields['file'].required = False

    def clean(self):
        cleaned_data = super().clean()
        service_type = cleaned_data.get('service_type')
        file = cleaned_data.get('file')

        if service_type == Service.PUBLIC and not file:
            raise forms.ValidationError("Para servicios públicos es obligatorio subir un archivo PDF.")
        if service_type == Service.COMMERCIAL and file:
            self.add_error('file', "Los servicios comerciales no deben tener archivo adjunto. Se ignorará.")
            cleaned_data['file'] = None

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance
