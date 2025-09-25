from django import forms
from django.forms import modelformset_factory
from django.core.validators import FileExtensionValidator
from django.db import models

from dashboard.models import ScientificPublication, Author


class ScientificPublicationForm(forms.ModelForm):
    author_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar autor por nombre, apellido o email'
        }),
        label="Buscar Autor Existente"
    )

    class Meta:
        model = ScientificPublication
        fields = ['title', 'publication_date', 'summary', 'pdf_file', 'author']
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
            'author': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filtrar autores existentes para el select
        self.fields['author'].queryset = Author.objects.all()
        self.fields['author'].required = True

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance


class CoauthorForm(forms.ModelForm):
    search_term = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar coautor existente'
        }),
        label="Buscar Coautor"
    )

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
        # Hacer campos opcionales
        for field in ['email', 'institution', 'orcid_id']:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        search_term = cleaned_data.get('search_term')
        email = cleaned_data.get('email')

        # Si se proporcionó un término de búsqueda, buscar autor existente
        if search_term:
            author = self.find_existing_author(search_term)
            if author:
                # Usar el autor existente
                self.instance = author
                # Actualizar los campos del formulario con los datos del autor existente
                for field in ['first_name', 'last_name', 'email', 'institution', 'orcid_id']:
                    if field in cleaned_data:
                        cleaned_data[field] = getattr(author, field)

        # Si no se encontró por búsqueda pero hay email, buscar por email
        elif email and not self.instance.pk:
            existing_author = Author.objects.filter(email=email).first()
            if existing_author:
                self.instance = existing_author
                for field in ['first_name', 'last_name', 'institution', 'orcid_id']:
                    if field in cleaned_data:
                        cleaned_data[field] = getattr(existing_author, field)

        return cleaned_data

    def find_existing_author(self, search_term):
        """Buscar autor existente por nombre, apellido o email"""
        if not search_term:
            return None

        # Buscar por email exacto
        author = Author.objects.filter(email__iexact=search_term).first()
        if author:
            return author

        # Buscar por nombre y apellido
        search_terms = search_term.split()
        if len(search_terms) >= 2:
            first_name = search_terms[0]
            last_name = ' '.join(search_terms[1:])
            author = Author.objects.filter(
                first_name__icontains=first_name,
                last_name__icontains=last_name
            ).first()
            if author:
                return author

        # Buscar por nombre o apellido
        author = Author.objects.filter(
            models.Q(first_name__icontains=search_term) |
            models.Q(last_name__icontains=search_term)
        ).first()

        return author

    def save(self, commit=True):
        # Si el autor ya existe, no guardar cambios (solo reutilizar)
        if self.instance.pk:
            return self.instance

        # Solo crear nuevo autor si no existe
        if not Author.objects.filter(
                models.Q(email=self.cleaned_data.get('email')) |
                models.Q(
                    first_name=self.cleaned_data.get('first_name'),
                    last_name=self.cleaned_data.get('last_name')
                )
        ).exists():
            return super().save(commit=commit)

        # Si existe, encontrar y retornar el autor existente
        if self.cleaned_data.get('email'):
            existing_author = Author.objects.filter(email=self.cleaned_data.get('email')).first()
            if existing_author:
                return existing_author

        existing_author = Author.objects.filter(
            first_name=self.cleaned_data.get('first_name'),
            last_name=self.cleaned_data.get('last_name')
        ).first()

        return existing_author or super().save(commit=commit)


# Formset para coautores
CoauthorFormSet = modelformset_factory(
    Author,
    form=CoauthorForm,
    extra=1,
    can_delete=True,
    min_num=0,  # Puede haber 0 coautores
    validate_min=True
)