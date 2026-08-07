from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.core.forms.company_settings import CompanySettingsForm
from apps.core.models import CompanySettings, SiteConfiguration


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


def disable_maintenance_mode():
    SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})


class CompanySettingsAjaxViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.url = reverse('core:company_settings_ajax')
        cls.other_user = User.objects.create_user(
            'worker',
            'worker@example.com',
            'password',
            first_name='Worker',
            last_name='User',
        )

    def test_anonymous_post_redirects_to_login(self):
        response = self.client.post(self.url, _valid_data())
        self.assertEqual(response.status_code, 302)

    def test_authenticated_without_permission_gets_403(self):
        self.client.force_login(self.other_user)
        response = self.client.post(self.url, _valid_data())
        self.assertEqual(response.status_code, 403)

    def test_authenticated_with_permission_valid_data_returns_success(self):
        user = User.objects.create_user(
            'admin_company',
            'admin_company@example.com',
            'password',
            first_name='Admin',
            last_name='Company',
        )
        user.user_permissions.add(*self._permissions('core', 'change_companysettings'))
        self.client.force_login(user)
        response = self.client.post(self.url, _valid_data())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True})

    def test_authenticated_with_permission_invalid_data_returns_errors(self):
        user = User.objects.create_user(
            'admin_company2',
            'admin_company2@example.com',
            'password',
            first_name='Admin',
            last_name='Company',
        )
        user.user_permissions.add(*self._permissions('core', 'change_companysettings'))
        self.client.force_login(user)
        data = _valid_data()
        data['nit'] = '123'
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body['success'])
        self.assertIn('nit', body['errors'])

    def _permissions(self, app_label, codename):
        from django.contrib.auth.models import Permission

        perm = Permission.objects.get(content_type__app_label=app_label, codename=codename)
        return [perm]


class ValidatePhonesSeparatorTests(TestCase):
    def setUp(self):
        self.instance = CompanySettings.get_instance()

    def test_leading_and_trailing_separators_are_trimmed(self):
        data = _valid_data()
        data['telefonos'] = ', 51234567,'
        form = CompanySettingsForm(data=data, instance=self.instance)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['telefonos'], '51234567')

    def test_slash_separator_is_rejected(self):
        data = _valid_data()
        data['telefonos'] = '51234567/32270000'
        form = CompanySettingsForm(data=data, instance=self.instance)
        self.assertFalse(form.is_valid())
        self.assertIn('telefonos', form.errors)
