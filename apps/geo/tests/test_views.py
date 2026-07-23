from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.dashboard.models import SiteConfiguration
from apps.geo.models import Province, Station


def _make_admin(username='admin', **kwargs):
    email = kwargs.pop('email', f'{username}@example.com')
    data = {'first_name': 'Admin', 'last_name': 'User'}
    data.update(kwargs)
    return User.objects.create_superuser(username, email, 'password', **data)


def _disable_maintenance():
    SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})


class ProvinceCRUDTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('provadmin')
        cls.list_url = reverse('geo:provincia_list')
        cls.create_url = reverse('geo:provincia_create')

    def test_list_view(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Listado de Provincias')

    def test_create_province(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.create_url, {'name': 'TestProv', 'code': 'TP'}, follow=True)
        self.assertTrue(Province.objects.filter(name='TestProv').exists())
        self.assertRedirects(response, self.list_url)

    def test_update_province(self):
        self.client.force_login(self.admin)
        prov = Province.objects.create(name='OldName', code='ON')
        url = reverse('geo:provincia_update', args=[prov.uuid])
        response = self.client.post(url, {'name': 'NewName', 'code': 'NN'}, follow=True)
        prov.refresh_from_db()
        self.assertEqual(prov.name, 'NewName')

    def test_delete_province(self):
        self.client.force_login(self.admin)
        prov = Province.objects.create(name='DeleteMe', code='DM')
        url = reverse('geo:provincia_delete', args=[prov.uuid])
        response = self.client.post(url, follow=True)
        self.assertFalse(Province.objects.filter(name='DeleteMe').exists())
        self.assertRedirects(response, self.list_url)


class StationCRUDTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('stnadmin')
        cls.prov = Province.objects.create(name='TestProv', code='TP')
        cls.list_url = reverse('geo:estacion_list')
        cls.create_url = reverse('geo:estacion_create')

    def test_list_view(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

    def test_create_station(self):
        self.client.force_login(self.admin)
        data = {
            'name': 'TestStation',
            'number': 999,
            'province': self.prov.pk,
            'latitude': 21.5,
            'longitude': -78.0,
        }
        response = self.client.post(self.create_url, data, follow=True)
        self.assertTrue(Station.objects.filter(name='TestStation').exists())
