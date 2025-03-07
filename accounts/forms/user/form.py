from django import forms
from django.contrib.auth.forms import *
from django.contrib.auth.models import *

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