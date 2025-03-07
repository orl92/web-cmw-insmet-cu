from django import forms
from django.contrib.auth.models import Group, Permission
from django.db.models import Q


class GroupForm(forms.ModelForm):

    class Meta:
        model = Group
        fields = ['name', 'permissions']
        widgets = {
            'permissions': forms.SelectMultiple(
                attrs={
                    'class': 'form-control',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['permissions'].queryset = Permission.objects.filter(
            Q(content_type__app_label='dashboard')
        )