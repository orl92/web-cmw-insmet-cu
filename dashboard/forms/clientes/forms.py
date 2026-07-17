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
            'address', 'phone', 'accept_terms', 'newsletter',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['accept_terms'].required = True
        for field_name, field in self.fields.items():
            if field_name not in ['username', 'password', 'email', 'accept_terms', 'newsletter']:
                field.widget.attrs.update({'class': 'form-control'})

    # --- Validaciones igual que antes ---
    def clean_reeup(self):
        reeup = self.cleaned_data.get('reeup')
        if reeup and not re.match(r'^\d{3}\.\d{1,2}\.\d{4,5}$', reeup):
            raise ValidationError("Formato inválido. Use ###.#.#### o ###.##.#####")
        return reeup

    def clean_nit(self):
        nit = self.cleaned_data.get('nit', '')
        validator = Customer._meta.get_field('nit').validators[0]
        validator(nit)
        return nit

    def clean_account(self):
        account = self.cleaned_data.get('account', '')
        validator = Customer._meta.get_field('account').validators[0]
        validator(account)
        return account

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        validator = Customer._meta.get_field('phone').validators[0]
        validator(phone)
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
            'address', 'phone', 'accept_terms', 'newsletter',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email
        self.fields['accept_terms'].required = True
        for field_name, field in self.fields.items():
            if field_name not in ['email', 'accept_terms', 'newsletter']:
                field.widget.attrs.update({'class': 'form-control'})

    # Validaciones (idénticas a las de CustomerForm)
    def clean_reeup(self):
        reeup = self.cleaned_data.get('reeup', '')
        validator = Customer._meta.get_field('reeup').validators[0]
        validator(reeup)
        return reeup

    def clean_nit(self):
        nit = self.cleaned_data.get('nit', '')
        validator = Customer._meta.get_field('nit').validators[0]
        validator(nit)
        return nit

    def clean_account(self):
        account = self.cleaned_data.get('account', '')
        validator = Customer._meta.get_field('account').validators[0]
        validator(account)
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
            'address', 'phone', 'accept_terms', 'newsletter',
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['email'].initial = self.user.email
        self.fields['accept_terms'].required = True
        for field_name, field in self.fields.items():
            if field_name not in ['email', 'accept_terms', 'newsletter']:
                field.widget.attrs.update({'class': 'form-control'})

    def clean_reeup(self):
        reeup = self.cleaned_data.get('reeup', '')
        validator = Customer._meta.get_field('reeup').validators[0]
        validator(reeup)
        return reeup

    def clean_nit(self):
        nit = self.cleaned_data.get('nit', '')
        validator = Customer._meta.get_field('nit').validators[0]
        validator(nit)
        return nit

    def clean_account(self):
        account = self.cleaned_data.get('account', '')
        validator = Customer._meta.get_field('account').validators[0]
        validator(account)
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
