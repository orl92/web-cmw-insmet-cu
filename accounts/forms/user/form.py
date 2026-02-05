# forms.py
import re

from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from dashboard.models import Customer, Service

# Create your form here.

class UserForm(UserCreationForm):
    
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    
class UserUpdateForm(UserChangeForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'is_superuser', 'groups']
        exclude = ['password', 'user_permissions']


class CustomerSignUpForm(UserCreationForm):
    # Campos del Paso 1: Datos Personales
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="Nombre",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Juan'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label="Apellido",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pérez'})
    )
    phone = forms.CharField(
        max_length=8,
        required=True,
        label="Número de Teléfono",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678'})
    )
    
    # Campos del Paso 2: Credenciales
    email = forms.EmailField(
        required=True,
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@empresa.com'})
    )
    
    # Campos del Paso 3: Empresa
    company_name = forms.CharField(
        max_length=100,
        required=True,
        label="Nombre de la Empresa",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mi Empresa S.A.'})
    )
    reeup = forms.CharField(
        max_length=11,
        required=True,
        label="REEUP",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678901'})
    )
    nit = forms.CharField(
        max_length=11,
        required=True,
        label="NIT",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678901'})
    )
    account = forms.CharField(
        max_length=16,
        required=True,
        label="Cuenta Bancaria",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1234567890123456'})
    )
    address = forms.CharField(
        required=True,
        label="Dirección",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Av. Principal 123'})
    )
    
    # Campos del Paso 4: Confirmación
    accept_terms = forms.BooleanField(
        required=True,
        label="Acepto los Términos y Condiciones",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    newsletter = forms.BooleanField(
        required=False,
        label="Deseo recibir novedades por correo electrónico",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'usuario_empresa'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '********'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '********'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Campos requeridos
        self.fields['accept_terms'].required = True
        self.fields['reeup'].required = True
        self.fields['nit'].required = True
        self.fields['account'].required = True
        self.fields['address'].required = True
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado.")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Este nombre de usuario ya existe.")
        return username
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r'^[0-9]{8}$', phone):
            raise ValidationError("El teléfono debe tener exactamente 8 dígitos numéricos.")
        return phone
    
    def clean_reeup(self):
        reeup = self.cleaned_data.get('reeup')
        if not re.match(r'^[0-9]{11}$', reeup):
            raise ValidationError("El REEUP debe tener exactamente 11 dígitos numéricos.")
        return reeup
    
    def clean_nit(self):
        nit = self.cleaned_data.get('nit')
        if not re.match(r'^[0-9]{11}$', nit):
            raise ValidationError("El NIT debe tener exactamente 11 dígitos numéricos.")
        return nit
    
    def clean_account(self):
        account = self.cleaned_data.get('account')
        if not re.match(r'^[0-9]{16}$', account):
            raise ValidationError("La cuenta bancaria debe tener exactamente 16 dígitos numéricos.")
        return account
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_active = True
        
        if commit:
            user.save()
            
            # Asignar al grupo "Clientes" si existe
            try:
                clientes_group = Group.objects.get(name='Clientes')
            except Group.DoesNotExist:
                # Crear grupo de Clientes
                clientes_group = Group.objects.create(name='Clientes')
                # Dar permiso para ver servicios
                service_content_type = ContentType.objects.get_for_model(Service)
                view_perm = Permission.objects.get(
                    content_type=service_content_type,
                    codename='view_service'
                )
                clientes_group.permissions.add(view_perm)
            
            user.groups.add(clientes_group)
            
            # Crear perfil de cliente con todos los campos
            Customer.objects.create(
                user=user,
                company_name=self.cleaned_data['company_name'],
                reeup=self.cleaned_data['reeup'],
                nit=self.cleaned_data['nit'],
                account=self.cleaned_data['account'],
                address=self.cleaned_data['address'],
                phone=self.cleaned_data['phone'],
                accept_terms=self.cleaned_data['accept_terms'],
                newsletter=self.cleaned_data.get('newsletter', False)
            )
        
        return user
