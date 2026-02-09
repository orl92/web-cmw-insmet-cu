from django import forms
from django.contrib.auth.models import User

from dashboard.models import Customer


class CustomerForm(forms.ModelForm):
    # Campos del User
    username = forms.CharField(max_length=150, required=True, label='Nombre de Usuario')
    password = forms.CharField(widget=forms.PasswordInput, required=True, label='Contraseña')
    email = forms.EmailField(required=True, label='Correo Electrónico')
    
    class Meta:
        model = Customer
        fields = "__all__"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agrega clases CSS si lo deseas
        for field in self.fields:
            if field not in ['username', 'password', 'email']:
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })

    def clean_reeup(self):
        reeup = self.cleaned_data.get('reeup', '')
        # Ejemplo de validación personalizada
        if not reeup.replace('.', '').isdigit():
            raise forms.ValidationError('El REEUP debe contener solo números y puntos.')
        return reeup
    
    def clean_nit(self):
        nit = self.cleaned_data.get('nit', '')
        if not nit.isdigit():
            raise forms.ValidationError('El NIT debe contener solo números.')
        return nit
    
    def clean_account(self):
        account = self.cleaned_data.get('account', '')
        if not account.isdigit():
            raise forms.ValidationError('La cuenta bancaria debe contener solo números.')
        if len(account) != 16:
            raise forms.ValidationError('La cuenta bancaria debe tener 16 dígitos.')
        return account
    
    def save(self, commit=True):
        customer = super().save(commit=False)
        
        # Crear usuario
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email']
        )
        customer.user = user
        
        if commit:
            customer.save()
        return customer


class CustomerUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Correo Electrónico')
    
    class Meta:
        model = Customer
        fields = "__all__"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        customer = super().save(commit=False)
        if commit:
            customer.save()
            # Actualizar email del usuario
            if customer.user and 'email' in self.cleaned_data:
                customer.user.email = self.cleaned_data['email']
                customer.user.save()
        return customer
