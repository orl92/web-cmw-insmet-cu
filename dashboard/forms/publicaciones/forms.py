from django import forms
from django.forms import inlineformset_factory
from django.core.validators import FileExtensionValidator

from dashboard.models import ScientificPublication, Author


class ScientificPublicationForm(forms.ModelForm):
    class Meta:
        model = ScientificPublication
        fields = ['title', 'publication_date', 'summary', 'pdf_file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la publicación científica'
            }),
            'publication_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Resumen de la publicación',
                'rows': 4
            }),
            'pdf_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['first_name', 'last_name', 'email', 'institution', 'orcid_id']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombres del autor'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellidos del autor'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Correo electrónico (opcional)'
            }),
            'institution': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Institución (opcional)'
            }),
            'orcid_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ORCID ID (opcional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos opcionales
        self.fields['email'].required = False
        self.fields['institution'].required = False
        self.fields['orcid_id'].required = False

    def clean_email(self):
        email = self.cleaned_data.get('email')

        # Si el email está vacío, permitirlo (es opcional)
        if not email:
            return email

        # Si el email no ha cambiado, no validar unicidad
        if self.instance.pk and self.instance.email == email:
            return email

        # Validar unicidad si es nuevo o ha cambiado
        if email and Author.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe un autor con este correo electrónico.")

        return email

    def clean_orcid_id(self):
        orcid_id = self.cleaned_data.get('orcid_id')

        # Si el ORCID ID está vacío, permitirlo (es opcional)
        if not orcid_id:
            return orcid_id

        # Validar formato básico de ORCID (XXXX-XXXX-XXXX-XXXX)
        if len(orcid_id) != 19 or orcid_id.count('-') != 3:
            raise forms.ValidationError("El formato del ORCID ID debe ser: XXXX-XXXX-XXXX-XXXX")

        # Si el ORCID ID no ha cambiado, no validar unicidad
        if self.instance.pk and self.instance.orcid_id == orcid_id:
            return orcid_id

        # Validar unicidad si es nuevo o ha cambiado
        if orcid_id and Author.objects.filter(orcid_id=orcid_id).exists():
            raise forms.ValidationError("Ya existe un autor con este ORCID ID.")

        return orcid_id


# Formset para autores (similar al ejemplo de EmailRecipient)
AuthorFormSet = inlineformset_factory(
    ScientificPublication,
    Author,
    form=AuthorForm,
    extra=1,  # Agregar 1 formulario vacío automáticamente
    can_delete=True,  # Permitir eliminación
    can_order=False,  # No permitir ordenar
    min_num=1,  # Mínimo 1 autor requerido
    validate_min=True  # Validar el mínimo
)
