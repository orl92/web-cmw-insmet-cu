from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.core.models import SiteConfiguration
from apps.meteo.models import Province, Station, Town


def _disable_maintenance_mode():
    SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})


class ProvinceListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance_mode()
        cls.admin = User.objects.create_superuser(
            'admin', 'admin@example.com', 'pass',
            first_name='Admin', last_name='User',
        )
        cls.province = Province.objects.create(name='Camagüey', code='09')
        for i in range(13):
            Town.objects.create(
                province=cls.province, name=f'Municipio {i}',
                latitude=21.5, longitude=-78.2,
            )
        for i in range(6):
            Station.objects.create(
                province=cls.province, name=f'Estación {i}', number=100 + i,
                latitude=21.5, longitude=-78.2,
            )

    def test_list_shows_town_and_station_counts(self):
        self.client.force_login(self.admin)
        url = reverse('meteo:provincia_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'badge badge-outline text-blue">13')
        self.assertContains(response, 'badge badge-outline text-green">6')
        self.assertNotContains(response, 'badge badge-outline text-blue">78')
        self.assertNotContains(response, 'badge badge-outline text-green">78')
