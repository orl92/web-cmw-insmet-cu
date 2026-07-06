
from django import forms
from django.contrib.auth.models import User

from accounts.models import Profile
from dashboard.models import Customer


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, label="Nombre")
    last_name = forms.CharField(max_length=30, required=True, label="Apellido")
    email = forms.EmailField(required=True, label="Correo electrónico")
    
    company_name = forms.CharField(max_length=100, required=False, label="Nombre de la Empresa",
                                   widget=forms.TextInput(attrs={'class': 'form-control'}))
    reeup = forms.CharField(max_length=12, required=False, label="REEUP",
                            widget=forms.TextInput(attrs={'class': 'form-control'}))
    nit = forms.CharField(max_length=11, required=False, label="NIT",
                          widget=forms.TextInput(attrs={'class': 'form-control'}))
    account = forms.CharField(max_length=16, required=False, label="Cuenta Bancaria",
                              widget=forms.TextInput(attrs={'class': 'form-control'}))
    agency_bank = forms.CharField(max_length=100, required=False, label="Agencia Bancaria",
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(required=False, label="Dirección",
                              widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
    phone = forms.CharField(max_length=8, required=False, label="Número de Teléfono",
                            widget=forms.TextInput(attrs={'class': 'form-control'}))
    newsletter = forms.BooleanField(required=False, label="Recibir novedades por email",
                                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model = Profile
        fields = ['avatar', 'first_name', 'last_name', 'email']
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance.user_id is not None:
            user = self.instance.user
            if hasattr(user, 'customer'):
                customer = user.customer
                self.fields['company_name'].initial = customer.company_name
                self.fields['reeup'].initial = customer.reeup
                self.fields['nit'].initial = customer.nit
                self.fields['account'].initial = customer.account
                self.fields['agency_bank'].initial = customer.agency_bank
                self.fields['address'].initial = customer.address
                self.fields['phone'].initial = customer.phone
                self.fields['newsletter'].initial = customer.newsletter
                
                # Campos obligatorios para clientes
                for field_name in ['company_name', 'reeup', 'nit', 'account',
                                   'agency_bank', 'address', 'phone']:
                    self.fields[field_name].required = True
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = self.instance.user
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            validator = Customer._meta.get_field('phone').validators[0]
            validator(phone)
        return phone
    
    def clean_reeup(self):
        reeup = self.cleaned_data.get('reeup')
        if reeup:
            validator = Customer._meta.get_field('reeup').validators[0]
            validator(reeup)
        return reeup
    
    def clean_nit(self):
        nit = self.cleaned_data.get('nit')
        if nit:
            validator = Customer._meta.get_field('nit').validators[0]
            validator(nit)
        return nit
    
    def clean_account(self):
        account = self.cleaned_data.get('account')
        if account:
            validator = Customer._meta.get_field('account').validators[0]
            validator(account)
        return account
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        if profile.user_id is None:
            raise ValueError("El perfil no tiene un usuario asociado.")
        
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            profile.save()
            
            if hasattr(user, 'customer'):
                customer = user.customer
                customer.company_name = self.cleaned_data.get('company_name', '')
                customer.reeup = self.cleaned_data.get('reeup', '')
                customer.nit = self.cleaned_data.get('nit', '')
                customer.account = self.cleaned_data.get('account', '')
                customer.agency_bank = self.cleaned_data.get('agency_bank', '')
                customer.address = self.cleaned_data.get('address', '')
                customer.phone = self.cleaned_data.get('phone', '')
                customer.newsletter = self.cleaned_data.get('newsletter', False)
                customer.save()
        
        return profile
