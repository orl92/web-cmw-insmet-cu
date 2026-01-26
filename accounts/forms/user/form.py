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
    email = forms.EmailField(
        required=True,
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@empresa.com'})
    )
    company_name = forms.CharField(
        max_length=100,
        label="Nombre de la Empresa",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mi Empresa S.A.'})
    )
    phone = forms.CharField(
        max_length=8,
        label="Número de Teléfono",
        widget=forms.TextInput(attrs={'class': 'form-control', 'pattern': '[0-9]{8}', 'placeholder': '12345678'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'company_name', 'phone']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'usuario_empresa'}),
        }
    
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
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
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
            
            # Crear perfil de cliente
            Customer.objects.create(
                user=user,
                company_name=self.cleaned_data['company_name'],
                phone=self.cleaned_data['phone']
            )
        
        return user
