from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from apps.commercial.models import Customer, ServiceSubscription
from apps.core.validators import validate_account, validate_nit, validate_phones, validate_reeup
from apps.user_auth.models import Profile


class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']


class UserUpdateForm(UserChangeForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    newsletter = forms.BooleanField(
        required=False,
        label='Recibe novedades por correo',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Grupos',
        required=False,
        help_text=(
            'Grupos a los que pertenece el usuario. Los permisos de estos grupos '
            'se aplican automáticamente.'
        ),
    )

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'is_staff',
            'is_active',
            'is_superuser',
            'groups',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            profile, _ = Profile.objects.get_or_create(user=self.instance)
            self.fields['newsletter'].initial = profile.newsletter

    def save(self, commit=True):
        user = super().save(commit=commit)
        newsletter = self.cleaned_data.get('newsletter', False)
        if commit:
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.newsletter = newsletter
            profile.save()
        return user


class CustomerSignUpForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label='Nombre',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Juan'}),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label='Apellido',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pérez'}),
    )
    phone = forms.CharField(
        max_length=100,
        required=True,
        label='Teléfonos',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': '51234567, 32270000'}
        ),
    )
    email = forms.EmailField(
        required=True,
        label='Correo electrónico',
        widget=forms.EmailInput(
            attrs={'class': 'form-control', 'placeholder': 'ejemplo@empresa.com'}
        ),
    )
    client_type = forms.ChoiceField(
        choices=Customer.ClientType.choices,
        initial=Customer.ClientType.JURIDICA,
        required=True,
        label='Tipo de Cliente',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
    )
    company_name = forms.CharField(
        max_length=100,
        required=False,
        label='Nombre de la Empresa o Razón Social',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mi Empresa S.A.'}),
    )
    reeup = forms.CharField(
        max_length=12,
        required=False,
        label='REEUP',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '211.0.6749'}),
    )
    nit = forms.CharField(
        max_length=11,
        required=False,
        label='NIT',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678901'}),
    )
    account = forms.CharField(
        max_length=16,
        required=True,
        label='Cuenta Bancaria',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1234567890123456'}),
    )
    agency_bank = forms.CharField(
        max_length=100,
        required=True,
        label='Agencia Bancaria',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'BPA, BFI, etc.'}),
    )
    address = forms.CharField(
        required=True,
        label='Dirección',
        widget=forms.Textarea(
            attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Av. Principal 123'}
        ),
    )
    accept_terms = forms.BooleanField(
        required=True,
        label='Acepto los Términos y Condiciones',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    newsletter = forms.BooleanField(
        required=False,
        label='Deseo recibir novedades por correo electrónico',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'usuario_empresa'}
            ),
            'password1': forms.PasswordInput(
                attrs={'class': 'form-control', 'placeholder': '********'}
            ),
            'password2': forms.PasswordInput(
                attrs={'class': 'form-control', 'placeholder': '********'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['accept_terms'].required = True
        self.fields['account'].required = True
        self.fields['address'].required = True
        self.fields['client_type'].widget.attrs.update({'class': 'form-check-input'})

        client_type = self.initial.get('client_type') or Customer.ClientType.JURIDICA
        if self.data.get('client_type'):
            client_type = self.data['client_type']
        if client_type == Customer.ClientType.JURIDICA:
            self.fields['company_name'].required = True
            self.fields['reeup'].required = True
            self.fields['nit'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Este nombre de usuario ya existe.')
        return username

    def clean_phone(self):
        return validate_phones(self.cleaned_data.get('phone'))

    def clean_reeup(self):
        reeup = self.cleaned_data.get('reeup')
        client_type = self.cleaned_data.get('client_type')
        if client_type == Customer.ClientType.JURIDICA:
            if not reeup:
                raise ValidationError('El REEUP es obligatorio para personas jurídicas.')
            validate_reeup(reeup)
            if Customer.objects.filter(reeup=reeup).exists():
                raise ValidationError('Este código REEUP ya está registrado.')
        return reeup

    def clean_nit(self):
        nit = self.cleaned_data.get('nit')
        client_type = self.cleaned_data.get('client_type')
        if client_type == Customer.ClientType.JURIDICA:
            if not nit:
                raise ValidationError('El NIT es obligatorio para personas jurídicas.')
            validate_nit(nit)
            if Customer.objects.filter(nit=nit).exists():
                raise ValidationError('Este NIT ya está registrado.')
        return nit

    def clean_account(self):
        account = self.cleaned_data.get('account')
        validate_account(account)
        return account

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_active = True

        if commit:
            user.save()

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.newsletter = self.cleaned_data.get('newsletter', False)
            profile.save()

            clientes_group, created = Group.objects.get_or_create(name='Clientes')
            if created:
                subscription_content_type = ContentType.objects.get_for_model(ServiceSubscription)
                view_perm = Permission.objects.get(
                    content_type=subscription_content_type, codename='view_subscription'
                )
                clientes_group.permissions.add(view_perm)
            user.groups.add(clientes_group)

            Customer.objects.create(
                user=user,
                client_type=self.cleaned_data['client_type'],
                company_name=self.cleaned_data.get('company_name') or None,
                reeup=self.cleaned_data.get('reeup') or None,
                nit=self.cleaned_data.get('nit') or None,
                account=self.cleaned_data['account'],
                agency_bank=self.cleaned_data.get('agency_bank') or '',
                address=self.cleaned_data['address'],
                phone=self.cleaned_data['phone'],
                accept_terms=self.cleaned_data['accept_terms'],
            )

        return user
