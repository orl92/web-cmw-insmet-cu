from django import forms
from django.contrib.auth.models import User

from dashboard.models import Customer


class CustomerForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, label='Nombre de Usuario')
    password = forms.CharField(widget=forms.PasswordInput, required=True, label='Contraseña')

    class Meta:
        model = Customer
        fields = ['username', 'password', 'company_name']

    def save(self, commit=True):
        customer = super().save(commit=False)
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password']
        )
        customer.user = user
        if commit:
            customer.save()
        return customer

class CustomerUpdateForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['company_name']
