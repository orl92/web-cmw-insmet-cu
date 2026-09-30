from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.commercial.models import Customer
from apps.core.validators import validate_account, validate_nit, validate_phones, validate_reeup

IDENTITY_REQUIRED_ERROR = 'El documento de identidad es obligatorio para personas naturales.'
IDENTITY_TAKEN_ERROR = 'Este documento de identidad ya está registrado.'


class CustomerForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, label='Nombre de Usuario')
    password = forms.CharField(widget=forms.PasswordInput, required=True, label='Contraseña')
    password2 = forms.CharField(
        widget=forms.PasswordInput, required=True, label='Confirmar Contraseña'
    )
    email = forms.EmailField(required=True, label='Correo Electrónico')

    class Meta:
        model = Customer
        fields = [
            'client_type',
            'identity_document',
            'company_name',
            'reeup',
            'nit',
            'account',
            'agency_bank',
            'address',
            'phone',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client_type'].widget = forms.RadioSelect(attrs={'class': 'form-check-input'})
        for field_name, field in self.fields.items():
            if field_name not in ['username', 'password', 'password2', 'email', 'client_type']:
                field.widget.attrs.update({'class': 'form-control'})
        self.fields['agency_bank'].required = True
        self._set_juridica_required()

    def _set_juridica_required(self):
        client_type = (
            self.data.get('client_type')
            or self.initial.get('client_type')
            or Customer.ClientType.JURIDICA
        )
        if client_type == Customer.ClientType.JURIDICA:
            self.fields['company_name'].required = True
            self.fields['reeup'].required = True
            self.fields['nit'].required = True
            self.fields['identity_document'].required = False
        else:
            self.fields['company_name'].required = False
            self.fields['reeup'].required = False
            self.fields['nit'].required = False
            self.fields['identity_document'].required = True

    def clean_identity_document(self):
        identity_document = (self.cleaned_data.get('identity_document') or '').strip()
        client_type = self.cleaned_data.get('client_type')
        if client_type == Customer.ClientType.NATURAL and not identity_document:
            raise ValidationError(IDENTITY_REQUIRED_ERROR)
        if not identity_document:
            return None
        if Customer.objects.filter(identity_document=identity_document).exists():
            raise ValidationError(IDENTITY_TAKEN_ERROR)
        return identity_document or None

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
        if Customer.objects.filter(account=account).exists():
            raise ValidationError('Esta cuenta bancaria ya está registrada.')
        return account

    def clean_phone(self):
        return validate_phones(self.cleaned_data.get('phone'))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        if password and password2 and password != password2:
            self.add_error('password2', 'Las contraseñas no coinciden.')
        return cleaned_data

    def save(self, commit=True):
        with transaction.atomic():
            customer = super().save(commit=False)
            if commit:
                user = User.objects.create_user(
                    username=self.cleaned_data['username'],
                    password=self.cleaned_data['password'],
                    email=self.cleaned_data['email'],
                )
                customer.user = user
                customer.save()
        return customer


class CustomerUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Correo Electrónico')

    class Meta:
        model = Customer
        fields = [
            'client_type',
            'identity_document',
            'company_name',
            'reeup',
            'nit',
            'account',
            'agency_bank',
            'address',
            'phone',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email
        self.fields['client_type'].widget = forms.RadioSelect(attrs={'class': 'form-check-input'})
        for field_name, field in self.fields.items():
            if field_name not in ['email', 'client_type']:
                field.widget.attrs.update({'class': 'form-control'})
        self.fields['agency_bank'].required = True
        self._set_juridica_required()

    def _set_juridica_required(self):
        client_type = (
            self.data.get('client_type')
            or self.initial.get('client_type')
            or (self.instance.client_type if self.instance.pk else Customer.ClientType.JURIDICA)
        )
        if client_type == Customer.ClientType.JURIDICA:
            self.fields['company_name'].required = True
            self.fields['reeup'].required = True
            self.fields['nit'].required = True
            self.fields['identity_document'].required = False
        else:
            self.fields['company_name'].required = False
            self.fields['reeup'].required = False
            self.fields['nit'].required = False
            self.fields['identity_document'].required = True

    def clean_identity_document(self):
        identity_document = (self.cleaned_data.get('identity_document') or '').strip()
        client_type = self.cleaned_data.get('client_type')
        if client_type == Customer.ClientType.NATURAL and not identity_document:
            raise ValidationError(IDENTITY_REQUIRED_ERROR)
        if not identity_document:
            return None
        qs = Customer.objects.filter(identity_document=identity_document).exclude(
            pk=self.instance.pk
        )
        if qs.exists():
            raise ValidationError(IDENTITY_TAKEN_ERROR)
        return identity_document or None

    def clean_reeup(self):
        reeup = self.cleaned_data.get('reeup', '')
        client_type = self.cleaned_data.get('client_type')
        if client_type == Customer.ClientType.JURIDICA:
            if not reeup:
                raise ValidationError('El REEUP es obligatorio para personas jurídicas.')
            validate_reeup(reeup)
            if Customer.objects.filter(reeup=reeup).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Este código REEUP ya está registrado.')
        return reeup

    def clean_nit(self):
        nit = self.cleaned_data.get('nit', '')
        client_type = self.cleaned_data.get('client_type')
        if client_type == Customer.ClientType.JURIDICA:
            if not nit:
                raise ValidationError('El NIT es obligatorio para personas jurídicas.')
            validate_nit(nit)
            if Customer.objects.filter(nit=nit).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Este NIT ya está registrado.')
        return nit

    def clean_account(self):
        account = self.cleaned_data.get('account', '')
        validate_account(account)
        if Customer.objects.filter(account=account).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Esta cuenta bancaria ya está registrada.')
        return account

    def clean_phone(self):
        return validate_phones(self.cleaned_data.get('phone', ''))

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
            'client_type',
            'identity_document',
            'company_name',
            'reeup',
            'nit',
            'account',
            'agency_bank',
            'address',
            'phone',
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['email'].initial = self.user.email
        self.fields['client_type'].widget = forms.RadioSelect(attrs={'class': 'form-check-input'})
        for field_name, field in self.fields.items():
            if field_name not in ['email', 'client_type']:
                field.widget.attrs.update({'class': 'form-control'})
        self.fields['agency_bank'].required = True
        self._set_juridica_required()

    def _set_juridica_required(self):
        client_type = (
            self.data.get('client_type')
            or self.initial.get('client_type')
            or (
                self.instance.client_type
                if self.instance and self.instance.pk
                else Customer.ClientType.JURIDICA
            )
        )
        if client_type == Customer.ClientType.JURIDICA:
            self.fields['company_name'].required = True
            self.fields['reeup'].required = True
            self.fields['nit'].required = True
            self.fields['identity_document'].required = False
        else:
            self.fields['company_name'].required = False
            self.fields['reeup'].required = False
            self.fields['nit'].required = False
            self.fields['identity_document'].required = True

    def clean_identity_document(self):
        identity_document = (self.cleaned_data.get('identity_document') or '').strip()
        client_type = self.cleaned_data.get('client_type')
        if client_type == Customer.ClientType.NATURAL and not identity_document:
            raise ValidationError(IDENTITY_REQUIRED_ERROR)
        if not identity_document:
            return None
        qs = Customer.objects.filter(identity_document=identity_document)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(IDENTITY_TAKEN_ERROR)
        return identity_document

    def clean_reeup(self):
        reeup = self.cleaned_data.get('reeup', '')
        client_type = self.cleaned_data.get('client_type')
        if client_type == Customer.ClientType.JURIDICA:
            if not reeup:
                raise ValidationError('El REEUP es obligatorio para personas jurídicas.')
            validate_reeup(reeup)
            if self.instance and self.instance.pk:
                if Customer.objects.filter(reeup=reeup).exclude(pk=self.instance.pk).exists():
                    raise ValidationError('Este código REEUP ya está registrado.')
            elif Customer.objects.filter(reeup=reeup).exists():
                raise ValidationError('Este código REEUP ya está registrado.')
        return reeup

    def clean_nit(self):
        nit = self.cleaned_data.get('nit', '')
        client_type = self.cleaned_data.get('client_type')
        if client_type == Customer.ClientType.JURIDICA:
            if not nit:
                raise ValidationError('El NIT es obligatorio para personas jurídicas.')
            validate_nit(nit)
            if self.instance and self.instance.pk:
                if Customer.objects.filter(nit=nit).exclude(pk=self.instance.pk).exists():
                    raise ValidationError('Este NIT ya está registrado.')
            elif Customer.objects.filter(nit=nit).exists():
                raise ValidationError('Este NIT ya está registrado.')
        return nit

    def clean_account(self):
        account = self.cleaned_data.get('account', '')
        validate_account(account)
        if self.instance and self.instance.pk:
            if Customer.objects.filter(account=account).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Esta cuenta bancaria ya está registrada.')
        elif Customer.objects.filter(account=account).exists():
            raise ValidationError('Esta cuenta bancaria ya está registrada.')
        return account

    def clean_phone(self):
        return validate_phones(self.cleaned_data.get('phone', ''))

    def save(self, commit=True):
        customer = super().save(commit=False)
        customer.user = self.user
        if commit:
            customer.save()
            if self.user and 'email' in self.cleaned_data:
                self.user.email = self.cleaned_data['email']
                self.user.save()
        return customer
