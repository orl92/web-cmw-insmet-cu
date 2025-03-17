from django import forms
from django.forms import inlineformset_factory
from dashboard.models import EmailRecipient, EmailRecipientList

class EmailRecipientListForm(forms.ModelForm):
    class Meta:
        model = EmailRecipientList
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la lista'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Descripción (opcional)', 'rows': 3}),
        }

class EmailRecipientForm(forms.ModelForm):
    class Meta:
        model = EmailRecipient
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False  # Permitir que el campo sea opcional

    def clean_email(self):
        email = self.cleaned_data.get('email')

        # Si el email no ha cambiado, no validar unicidad
        if self.instance.pk and self.instance.email == email:
            return email

        # Validar unicidad si es nuevo o ha cambiado
        if email and EmailRecipient.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe un/a Destinatario de Correo con este/a Correo Electrónico.")
        
        return email

EmailRecipientFormSet = inlineformset_factory(
    EmailRecipientList,
    EmailRecipient,
    form=EmailRecipientForm,
    extra=1,                  # Un formulario adicional vacío
    can_delete=True           # Permitir eliminación
)
