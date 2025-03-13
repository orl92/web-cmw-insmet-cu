from django import forms
from django.forms import inlineformset_factory
from dashboard.models import EmailRecipient, EmailRecipientList

# Formulario para la lista de correos
class EmailRecipientListForm(forms.ModelForm):
    class Meta:
        model = EmailRecipientList
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la lista'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción (opcional)',
                'rows': 3
            }),
        }

# Formulario para los destinatarios
class EmailRecipientForm(forms.ModelForm):
    class Meta:
        model = EmailRecipient
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Correo electrónico'
            }),
        }

# Formset para manejar destinatarios relacionados con una lista de correos
EmailRecipientFormSet = inlineformset_factory(
    EmailRecipientList,  # Modelo principal
    EmailRecipient,  # Modelo relacionado
    form=EmailRecipientForm,  # Formulario para destinatarios
    extra=1,  # Número de formularios vacíos adicionales
    can_delete=True  # Permitir eliminar destinatarios existentes
)
