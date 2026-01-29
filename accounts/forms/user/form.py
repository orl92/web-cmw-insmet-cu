from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError

from dashboard.models import Customer

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
    ci = forms.CharField(
        max_length=20,
        required=True,
        label="Documento de Identidad (CI)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de Carnet de Identidad'})
    )
    phone = forms.CharField(
        max_length=8,
        required=True,
        label="Número de Teléfono",
        widget=forms.TextInput(attrs={'class': 'form-control', 'pattern': '[0-9]{8}', 'placeholder': '12345678'})
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
    reup = forms.CharField(
        max_length=11,
        required=True,
        label="REEUP",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de REEUP (11 dígitos)'})
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
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Campos requeridos
        self.fields['accept_terms'].required = True
        self.fields['reup'].required = True
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
        if not phone.isdigit() or len(phone) != 8:
            raise ValidationError("El teléfono debe tener 8 dígitos numéricos.")
        return phone
    
    def clean_reup(self):
        reup = self.cleaned_data.get('reup', '')
        if not reup.isdigit() or len(reup) != 11:
            raise ValidationError("El REEUP debe tener 11 dígitos numéricos.")
        return reup
    
    def clean_ci(self):
        ci = self.cleaned_data.get('ci', '')
        # Validación básica para CI, puede ser alfanumérico
        if not ci:
            raise ValidationError("El documento de identidad es requerido.")
        return ci
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_active = True
        
        if commit:
            user.save()
            
            # Asignar al grupo "clientes" si existe
            try:
                clientes_group = Group.objects.get(name='clientes')
            except Group.DoesNotExist:
                # Crear grupo de clientes
                clientes_group = Group.objects.create(name='clientes')
                # Opcional: asignar permisos básicos aquí
                from django.contrib.auth.models import Permission
                from django.contrib.contenttypes.models import ContentType

                from dashboard.models import Service
                
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
                reup=self.cleaned_data['reup'],
                address=self.cleaned_data['address'],
                ci=self.cleaned_data['ci'],
                phone=self.cleaned_data['phone'],
                accept_terms=self.cleaned_data['accept_terms'],
                newsletter=self.cleaned_data.get('newsletter', False)
            )
        
        return user