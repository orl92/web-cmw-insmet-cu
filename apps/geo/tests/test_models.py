from django.test import TestCase

from apps.geo.models import Province, Station, Town


class ProvinceTests(TestCase):
    def test_create_province(self):
        p = Province.objects.create(name='Camagüey', code='CM')
        self.assertEqual(str(p), 'Camagüey')
        self.assertIsNotNone(p.uuid)

    def test_code_unique(self):
        Province.objects.create(name='Camagüey', code='CM')
        with self.assertRaises(Exception):
            Province.objects.create(name='Otro', code='CM')


class TownTests(TestCase):
    def test_create_town(self):
        prov = Province.objects.create(name='Camagüey', code='CM')
        town = Town.objects.create(name='Florida', province=prov, latitude=21.5, longitude=-78.2)
        self.assertEqual(str(town), 'Florida')
        self.assertEqual(town.province, prov)


class StationTests(TestCase):
    def test_create_station(self):
        prov = Province.objects.create(name='Camagüey', code='CM')
        station = Station.objects.create(name='Florida', number=123, province=prov, latitude=21.5, longitude=-78.2)
        self.assertEqual(str(station), 'Florida')
        self.assertEqual(station.number, 123)
