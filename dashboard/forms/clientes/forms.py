import re

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from dashboard.models import Customer


class CustomerForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, label='Nombre de Usuario')
    password = forms.CharField(widget=forms.PasswordInput, required=True, label='Contraseña')
    email = forms.EmailField(required=True, label='Correo Electrónico')

    class Meta:
        model = Customer
        fields = [
            'company_name', 'reeup', 'nit', 'account', 'agency_bank',
            'address', 'phone',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['username', 'password', 'email']:
                field.widget.attrs.update({'class': 'form-control'})

    # --- Validaciones igual que antes ---
    def clean_reeup(self):
        reeup = self.cleaned_data.get('reeup')
        if reeup:
            if not re.match(r'^\d{3}\.\d{1,2}\.\d{4,5}$', reeup):
                raise ValidationError("El REEUP debe tener el formato ###.#.#### o ###.##.#####")
            if Customer.objects.filter(reeup=reeup).exists():
                raise ValidationError("Este código REEUP ya está registrado.")
        return reeup

    def clean_nit(self):
        nit = self.cleaned_data.get('nit')
        if nit:
            if not re.match(r'^\d{11}$', nit):
                raise ValidationError("El NIT debe tener exactamente 11 dígitos numéricos.")
            if Customer.objects.filter(nit=nit).exists():
                raise ValidationError("Este NIT ya está registrado.")
        return nit

    def clean_account(self):
        account = self.cleaned_data.get('account')
        if not re.match(r'^\d{16}$', account):
            raise ValidationError("La cuenta bancaria debe tener exactamente 16 dígitos numéricos.")
        if Customer.objects.filter(account=account).exists():
            raise ValidationError("Esta cuenta bancaria ya está registrada.")
        return account

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r'^\d{8}$', phone):
            raise ValidationError("El teléfono debe tener exactamente 8 dígitos numéricos.")
        return phone

    def save(self, commit=True):
        customer = super().save(commit=False)
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
        fields = [
            'company_name', 'reeup', 'nit', 'account', 'agency_bank',
            'address', 'phone',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email
        for field_name, field in self.fields.items():
            if field_name not in ['email']:
                field.widget.attrs.update({'class': 'form-control'})

    # Validaciones (idénticas a las de CustomerForm)
    def clean_reeup(self):
        reeup = self.cleaned_data.get('reeup', '')
        validator = Customer._meta.get_field('reeup').validators[0]
        validator(reeup)
        if Customer.objects.filter(reeup=reeup).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Este código REEUP ya está registrado.")
        return reeup

    def clean_nit(self):
        nit = self.cleaned_data.get('nit', '')
        validator = Customer._meta.get_field('nit').validators[0]
        validator(nit)
        if Customer.objects.filter(nit=nit).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Este NIT ya está registrado.")
        return nit

    def clean_account(self):
        account = self.cleaned_data.get('account', '')
        validator = Customer._meta.get_field('account').validators[0]
        validator(account)
        if Customer.objects.filter(account=account).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Esta cuenta bancaria ya está registrada.")
        return account

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        validator = Customer._meta.get_field('phone').validators[0]
        validator(phone)
        return phone

    def save(self, commit=True):
        customer = super().save(commit=False)
        if commit:
            customer.save()
            if customer.user and 'email' in self.cleaned_data:
                customer.user.email = self.cleaned_data['email']
                customer.user.save()
        return customer


class CustomerForUserForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Correo Electrónico')

    class Meta:
        model = Customer
        fields = [
            'company_name', 'reeup', 'nit', 'account', 'agency_bank',
            'address', 'phone',
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['email'].initial = self.user.email
        for field_name, field in self.fields.items():
            if field_name not in ['email']:
                field.widget.attrs.update({'class': 'form-control'})

    def clean_reeup(self):
        reeup = self.cleaned_data.get('reeup', '')
        validator = Customer._meta.get_field('reeup').validators[0]
        validator(reeup)
        if self.instance and self.instance.pk:
            if Customer.objects.filter(reeup=reeup).exclude(pk=self.instance.pk).exists():
                raise ValidationError("Este código REEUP ya está registrado.")
        elif Customer.objects.filter(reeup=reeup).exists():
            raise ValidationError("Este código REEUP ya está registrado.")
        return reeup

    def clean_nit(self):
        nit = self.cleaned_data.get('nit', '')
        validator = Customer._meta.get_field('nit').validators[0]
        validator(nit)
        if self.instance and self.instance.pk:
            if Customer.objects.filter(nit=nit).exclude(pk=self.instance.pk).exists():
                raise ValidationError("Este NIT ya está registrado.")
        elif Customer.objects.filter(nit=nit).exists():
            raise ValidationError("Este NIT ya está registrado.")
        return nit

    def clean_account(self):
        account = self.cleaned_data.get('account', '')
        validator = Customer._meta.get_field('account').validators[0]
        validator(account)
        if self.instance and self.instance.pk:
            if Customer.objects.filter(account=account).exclude(pk=self.instance.pk).exists():
                raise ValidationError("Esta cuenta bancaria ya está registrada.")
        elif Customer.objects.filter(account=account).exists():
            raise ValidationError("Esta cuenta bancaria ya está registrada.")
        return account

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        validator = Customer._meta.get_field('phone').validators[0]
        validator(phone)
        return phone

    def save(self, commit=True):
        customer = super().save(commit=False)
        customer.user = self.user
        if commit:
            customer.save()
            if self.user and 'email' in self.cleaned_data:
                self.user.email = self.cleaned_data['email']
                self.user.save()
        return customer
