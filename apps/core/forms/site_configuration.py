import re

from django import forms

from apps.core.models import SiteConfiguration

HEX_COLOR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')


class SiteConfigurationForm(forms.ModelForm):
    class Meta:
        model = SiteConfiguration
        fields = [
            'primary_color',
            'theme_base',
            'theme_font',
            'theme_radius',
            'brand_logo',
            'favicon',
        ]
        widgets = {
            'primary_color': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'data-coloris': '',
                    'data-coloris-format': 'hex',
                    'placeholder': '#2b4b9b',
                }
            ),
            'theme_base': forms.Select(attrs={'class': 'form-select'}),
            'theme_font': forms.Select(attrs={'class': 'form-select'}),
            'theme_radius': forms.Select(attrs={'class': 'form-select'}),
            'brand_logo': forms.FileInput(attrs={'class': 'form-control'}),
            'favicon': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_primary_color(self):
        value = self.cleaned_data.get('primary_color')
        if not HEX_COLOR_RE.match(value):
            raise forms.ValidationError('El color debe tener formato #RRGGBB.')
        return value
