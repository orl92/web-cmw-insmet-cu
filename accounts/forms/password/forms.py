from django import forms
from datetime import datetime
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='Contraseña Actual',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password1 = forms.CharField(
        label='Nueva Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password2 = forms.CharField(
        label='Confirmar Nueva Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class AdminPasswordChangeForm(forms.ModelForm):
    new_password1 = forms.CharField(label='Nueva contraseña', widget=forms.PasswordInput)
    new_password2 = forms.CharField(label='Confirmar nueva contraseña', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = []

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["new_password1"])
        if commit:
            user.save()
        return user

class UserPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # Extraer la solicitud del formulario
        super().__init__(*args, **kwargs)

    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name=None):
        # Construir la URL completa al índice
        index_url = self.request.build_absolute_uri(reverse('index'))
        context['index_url'] = index_url  # Pasar la URL al contexto del correo

        # Construir la URL completa para el enlace de restablecimiento
        reset_url = self.request.build_absolute_uri(
            reverse('password_reset_confirm', kwargs={
                'uidb64': context['uid'],  # UID codificado
                'token': context['token'],  # Token generado
            })
        )
        context['reset_url'] = reset_url  # Pasar la URL al contexto del correo

        # Agregar el año actual al contexto
        context['current_year'] = datetime.now().year

        # Llamar al método base para enviar el correo
        html_email_template_name = 'pages/accounts/emails/password_reset_email.html'  # Template HTML personalizado
        super().send_mail(subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise ValidationError("La dirección de correo electrónico no es valida.")
        return email

