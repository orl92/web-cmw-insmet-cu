from datetime import date, time, timedelta

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from dashboard.models import Forecasts, Province, SiteConfiguration, Station


class StationListAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(pk=1, defaults={'maintenance_mode': False})
        SiteConfiguration.objects.filter(pk=1).update(maintenance_mode=False)
        prov = Province.objects.create(name='Camagüey', code='CM')
        Station.objects.create(name='Florida', number=123, province=prov,
                               latitude=21.5, longitude=-78.2)
        Station.objects.create(name='Camagüey', number=456, province=prov,
                               latitude=21.4, longitude=-77.9)
        cls.url = reverse('station-list')

    def test_list_returns_all_stations(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_station_has_expected_fields(self):
        response = self.client.get(self.url)
        station = response.data[0]
        self.assertIn('name', station)
        self.assertIn('province_name', station)


class ForecastAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        from dashboard.models import ForecastExtendedDay, ForecastRegions
        SiteConfiguration.objects.get_or_create(pk=1, defaults={'maintenance_mode': False})
        SiteConfiguration.objects.filter(pk=1).update(maintenance_mode=False)
        today = date.today()
        forecast = Forecasts.objects.create(
            date=today,
            lp='Luna Nueva', nlp='Cuarto Creciente', nlpd=today + timedelta(days=7),
            sunrise=time(6, 30), sunset=time(18, 30), uv_index=5,
        )
        regions_data = [
            ('north', 'morning', 25, 'PN', 'N', '10', 'TQ'),
            ('north', 'afternoon', 30, 'N', 'NE', '15', 'PO'),
            ('north', 'night', 22, 'PARCN', 'E', '5', 'TQ'),
            ('interior', 'morning', 24, 'PN', 'N', '10', None),
            ('interior', 'afternoon', 29, 'N', 'NE', '15', None),
            ('interior', 'night', 21, 'PARCN', 'E', '5', None),
            ('south', 'morning', 23, 'PN', 'N', '10', 'TQ'),
            ('south', 'afternoon', 28, 'N', 'NE', '15', 'PO'),
            ('south', 'night', 20, 'PARCN', 'E', '5', 'TQ'),
        ]
        for region, period, temp, weather, wind_dir, wind_speed, sea in regions_data:
            ForecastRegions.objects.create(
                forecast=forecast, region=region, period=period,
                temp=temp, weather=weather, wind_dir=wind_dir,
                wind_speed=wind_speed, sea_note=sea,
            )
        for i in range(1, 6):
            ForecastExtendedDay.objects.create(
                forecast=forecast, day_number=i,
                date=today + timedelta(days=i),
                min_temp=20, max_temp=30, weather='PN',
            )
        cls.url = reverse('forecast', args=[today.isoformat()])

    def test_forecast_detail_returns_data(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('north', response.data)
        self.assertIn('interior', response.data)
        self.assertIn('south', response.data)

    def test_forecast_not_found(self):
        url = reverse('forecast', args=['2099-01-01'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_forecast_has_region_periods(self):
        response = self.client.get(self.url)
        for region in ('north', 'interior', 'south'):
            self.assertIn(region, response.data)
            for period in ('morning', 'afternoon', 'night'):
                self.assertIn(period, response.data[region])
                self.assertIn('temp', response.data[region][period])

    def test_forecast_has_extended_days(self):
        response = self.client.get(self.url)
        self.assertIn('extended_forecast', response.data)
        self.assertEqual(len(response.data['extended_forecast']), 5)

    def test_schema_endpoint_returns_200(self):
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
