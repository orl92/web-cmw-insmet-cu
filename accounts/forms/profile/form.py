import re

from accounts.models import Profile
from django import forms
from django.contrib.auth.models import User


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, label="Nombre")
    last_name = forms.CharField(max_length=30, required=True, label="Apellido")
    email = forms.EmailField(required=True, label="Correo electrónico")
    
    # Campos de Customer (solo para clientes)
    company_name = forms.CharField(
        max_length=100, 
        required=False, 
        label="Nombre de la Empresa",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    reeup = forms.CharField(
        max_length=11, 
        required=False, 
        label="REEUP",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    nit = forms.CharField(
        max_length=11, 
        required=False, 
        label="NIT",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    account = forms.CharField(
        max_length=16, 
        required=False, 
        label="Cuenta Bancaria",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        required=False, 
        label="Dirección",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    phone = forms.CharField(
        max_length=8, 
        required=False, 
        label="Número de Teléfono",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    newsletter = forms.BooleanField(
        required=False, 
        label="Recibir novedades por email",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Profile
        fields = ['avatar', 'first_name', 'last_name', 'email']
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # --- CORRECCIÓN: Verificar que el perfil tenga un usuario asociado antes de acceder a customer ---
        if self.instance.user_id is not None:
            user = self.instance.user  # ahora es seguro acceder
            if hasattr(user, 'customer'):
                customer = user.customer
                self.fields['company_name'].initial = customer.company_name
                self.fields['reeup'].initial = customer.reeup
                self.fields['nit'].initial = customer.nit
                self.fields['account'].initial = customer.account
                self.fields['address'].initial = customer.address
                self.fields['phone'].initial = customer.phone
                self.fields['newsletter'].initial = customer.newsletter
                
                # Hacer campos requeridos para clientes
                self.fields['company_name'].required = True
                self.fields['reeup'].required = True
                self.fields['nit'].required = True
                self.fields['account'].required = True
                self.fields['address'].required = True
                self.fields['phone'].required = True
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = self.instance.user
        # Verificar que el email no esté en uso por otro usuario
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not re.match(r'^[0-9]{8}$', phone):
            raise forms.ValidationError("El teléfono debe tener exactamente 8 dígitos numéricos.")
        return phone
    
    def clean_reeup(self):
        reeup = self.cleaned_data.get('reeup')
        if reeup and not re.match(r'^[0-9]{11}$', reeup):
            raise forms.ValidationError("El REEUP debe tener exactamente 11 dígitos numéricos.")
        return reeup
    
    def clean_nit(self):
        nit = self.cleaned_data.get('nit')
        if nit and not re.match(r'^[0-9]{11}$', nit):
            raise forms.ValidationError("El NIT debe tener exactamente 11 dígitos numéricos.")
        return nit
    
    def clean_account(self):
        account = self.cleaned_data.get('account')
        if account and not re.match(r'^[0-9]{16}$', account):
            raise forms.ValidationError("La cuenta bancaria debe tener exactamente 16 dígitos numéricos.")
        return account
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # --- CORRECCIÓN: Asegurar que el perfil tiene un usuario antes de continuar ---
        if profile.user_id is None:
            raise ValueError("El perfil no tiene un usuario asociado. No se puede guardar.")
        
        user = profile.user
        
        # Actualizar datos del User
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            profile.save()
            
            # Actualizar datos del Customer si existe
            if hasattr(user, 'customer'):
                customer = user.customer
                customer.company_name = self.cleaned_data.get('company_name', '')
                customer.reeup = self.cleaned_data.get('reeup', '')
                customer.nit = self.cleaned_data.get('nit', '')
                customer.account = self.cleaned_data.get('account', '')
                customer.address = self.cleaned_data.get('address', '')
                customer.phone = self.cleaned_data.get('phone', '')
                customer.newsletter = self.cleaned_data.get('newsletter', False)
                customer.save()
        
        return profile
