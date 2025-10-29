from django import forms
from django.forms import modelformset_factory
from django.core.validators import FileExtensionValidator
from django.db import models

from dashboard.models import ScientificPublication, Author


class ScientificPublicationForm(forms.ModelForm):
    # Campos para el autor principal (igual que los coautores)
    author_first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombres del autor'
        }),
        label="Nombres del Autor",
        required=True
    )

    author_last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellidos del autor'
        }),
        label="Apellidos del Autor",
        required=True
    )

    author_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico del autor'
        }),
        label="Correo del Autor",
        required=False
    )

    author_institution = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Institución del autor'
        }),
        label="Institución del Autor",
        required=False
    )

    author_orcid_id = forms.CharField(
        max_length=19,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ORCID ID del autor'
        }),
        label="ORCID ID del Autor",
        required=False
    )

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

        # Si es una instancia existente y tiene autor, cargar los datos del autor
        if self.instance and self.instance.pk and hasattr(self.instance, 'author'):
            self.fields['author_first_name'].initial = self.instance.author.first_name
            self.fields['author_last_name'].initial = self.instance.author.last_name
            self.fields['author_email'].initial = self.instance.author.email
            self.fields['author_institution'].initial = self.instance.author.institution
            self.fields['author_orcid_id'].initial = self.instance.author.orcid_id

    def clean(self):
        cleaned_data = super().clean()
        author_first_name = cleaned_data.get('author_first_name')
        author_last_name = cleaned_data.get('author_last_name')

        # Validar que el autor principal tenga al menos nombre y apellido
        if not author_first_name or not author_last_name:
            raise forms.ValidationError("El autor principal debe tener al menos nombre y apellido.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Crear o obtener el autor principal usando get_or_create
        author_first_name = self.cleaned_data.get('author_first_name')
        author_last_name = self.cleaned_data.get('author_last_name')
        author_email = self.cleaned_data.get('author_email')

        if author_email:
            author, created = Author.objects.get_or_create(
                email=author_email,
                defaults={
                    'first_name': author_first_name,
                    'last_name': author_last_name,
                    'institution': self.cleaned_data.get('author_institution', ''),
                    'orcid_id': self.cleaned_data.get('author_orcid_id', '')
                }
            )
        else:
            author, created = Author.objects.get_or_create(
                first_name=author_first_name,
                last_name=author_last_name,
                defaults={
                    'email': author_email,
                    'institution': self.cleaned_data.get('author_institution', ''),
                    'orcid_id': self.cleaned_data.get('author_orcid_id', '')
                }
            )

        # Si no es nuevo, actualizar los campos si están vacíos
        if not created:
            author.email = self.cleaned_data.get('author_email')
            author.first_name = self.cleaned_data.get('author_first_name')
            author.last_name = self.cleaned_data.get('author_last_name')
            author.institution = self.cleaned_data.get('author_institution')
            author.orcid_id = self.cleaned_data.get('author_orcid_id')
            author.save()

        instance.author = author

        if self.user:
            instance.user = self.user

        if commit:
            instance.save()

        return instance


class CoauthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['first_name', 'last_name', 'email', 'institution', 'orcid_id']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombres'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellidos'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Correo electrónico'
            }),
            'institution': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Institución'
            }),
            'orcid_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ORCID ID'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos opcionales excepto nombre y apellido
        self.fields['email'].required = False
        self.fields['institution'].required = False
        self.fields['orcid_id'].required = False

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')

        # Validar que al menos tenga nombre y apellido
        if not first_name or not last_name:
            raise forms.ValidationError("El coautor debe tener al menos nombre y apellido.")

        return cleaned_data

    def save(self, commit=True):
        # Usar get_or_create para evitar duplicados
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')
        email = self.cleaned_data.get('email')

        if email:
            # Buscar por email si está disponible
            author, created = Author.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'institution': self.cleaned_data.get('institution', ''),
                    'orcid_id': self.cleaned_data.get('orcid_id', '')
                }
            )
        else:
            # Buscar por nombre y apellido si no hay email
            author, created = Author.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                defaults={
                    'email': email,
                    'institution': self.cleaned_data.get('institution', ''),
                    'orcid_id': self.cleaned_data.get('orcid_id', '')
                }
            )

        # Si no es nuevo, actualizar los campos si están vacíos
        if not created:
            if not author.email and email:
                author.email = email
            if not author.institution and self.cleaned_data.get('institution'):
                author.institution = self.cleaned_data.get('institution')
            if not author.orcid_id and self.cleaned_data.get('orcid_id'):
                author.orcid_id = self.cleaned_data.get('orcid_id')
            if commit:
                author.save()

        return author


# Formset para coautores
CoauthorFormSet = modelformset_factory(
    Author,
    form=CoauthorForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=True
)
