from django import forms

from apps.user_auth.models import PermissionProfile


class PermissionProfileForm(forms.ModelForm):
    class Meta:
        model = PermissionProfile
        fields = ['name', 'description', 'permissions']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'permissions': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 15}),
        }
