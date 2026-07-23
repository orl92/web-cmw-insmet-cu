from django.test import TestCase

from apps.geo.forms import ProvinceForm


class ProvinceFormTests(TestCase):
    def test_valid_data(self):
        form = ProvinceForm(data={'name': 'Camagüey', 'code': '09'})
        self.assertTrue(form.is_valid())

    def test_code_numeric(self):
        form = ProvinceForm(data={'name': 'Camagüey', 'code': 'abc'})
        self.assertFalse(form.is_valid())
        self.assertIn('code', form.errors)

    def test_blank_data(self):
        form = ProvinceForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('code', form.errors)
