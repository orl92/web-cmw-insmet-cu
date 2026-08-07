from django.test import TestCase

from apps.core.forms.company_settings import CompanySettingsForm
from apps.core.models import CompanySettings


def _valid_data():
    return {
        'nombre': 'Centro Meteorológico Provincial Camagüey',
        'direccion': 'Calle 1ra #120, Camagüey, Cuba',
        'codigo_reeup': '123.1.1234',
        'nit': '12345678901',
        'cuenta_bancaria': '1234567890123456',
        'agencia_bancaria': 'Banco de Crédito y Comercio',
        'telefonos': '32270000, 32270001',
        'registro_comercial': 'A09404',
    }


class CompanySettingsFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.instance = CompanySettings.get_instance()

    def test_valid_form(self):
        form = CompanySettingsForm(data=_valid_data(), instance=self.instance)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_reeup(self):
        data = _valid_data()
        data['codigo_reeup'] = '1234'
        form = CompanySettingsForm(data=data, instance=self.instance)
        self.assertFalse(form.is_valid())
        self.assertIn('codigo_reeup', form.errors)

    def test_invalid_nit(self):
        data = _valid_data()
        data['nit'] = '123'
        form = CompanySettingsForm(data=data, instance=self.instance)
        self.assertFalse(form.is_valid())
        self.assertIn('nit', form.errors)

    def test_invalid_account(self):
        data = _valid_data()
        data['cuenta_bancaria'] = '123456789012345'
        form = CompanySettingsForm(data=data, instance=self.instance)
        self.assertFalse(form.is_valid())
        self.assertIn('cuenta_bancaria', form.errors)

    def test_invalid_phones(self):
        data = _valid_data()
        data['telefonos'] = '51234567, 32270'
        form = CompanySettingsForm(data=data, instance=self.instance)
        self.assertFalse(form.is_valid())
        self.assertIn('telefonos', form.errors)

    def test_multi_phone_valid(self):
        data = _valid_data()
        data['telefonos'] = '51234567, 32270000-12345678; 55556666'
        form = CompanySettingsForm(data=data, instance=self.instance)
        self.assertTrue(form.is_valid(), form.errors)

    def test_required_fields_invalid(self):
        data = _valid_data()
        for field in ('codigo_reeup', 'nit', 'cuenta_bancaria', 'telefonos'):
            data[field] = ''
        form = CompanySettingsForm(data=data, instance=self.instance)
        self.assertFalse(form.is_valid())
        for field in ('codigo_reeup', 'nit', 'cuenta_bancaria', 'telefonos'):
            self.assertIn(field, form.errors)
