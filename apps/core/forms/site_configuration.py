import re

from django import forms

from apps.core.models import SiteConfiguration

HEX_COLOR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')


class SiteConfigurationForm(forms.ModelForm):
    class Meta:
        model = SiteConfiguration
        fields = ['primary_color', 'theme_base', 'brand_logo', 'favicon']
        widgets = {
            'primary_color': forms.TextInput(
                attrs={'type': 'color', 'class': 'form-control form-control-color'}
            ),
            'theme_base': forms.Select(attrs={'class': 'form-select'}),
            'brand_logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'favicon': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_primary_color(self):
        value = self.cleaned_data.get('primary_color')
        if not HEX_COLOR_RE.match(value):
            raise forms.ValidationError('El color debe tener formato #RRGGBB.')
        return value
