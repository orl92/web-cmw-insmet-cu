from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from dashboard.models import (
    Author,
    EarlyWarning,
    Forecasts,
    Province,
    ScientificPublication,
    Service,
    SiteConfiguration,
    Station,
    StormWarning,
    TropicalCyclone,
    WeatherReport,
)


class StationListAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(pk=1, defaults={'maintenance_mode': False})
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


class EarlyWarningAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(pk=1, defaults={'maintenance_mode': False})
        user = User.objects.create_user('testuser')
        EarlyWarning.objects.create(
            user=user, summary='Alerta activa',
            valid_until=timezone.now() + timedelta(days=1),
        )
        EarlyWarning.objects.create(
            user=user, summary='Alerta expirada',
            valid_until=timezone.now() - timedelta(days=1),
        )
        cls.url = reverse('early-warning-list')

    def test_list_returns_only_active(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_has_expected_fields(self):
        response = self.client.get(self.url)
        item = response.data[0]
        self.assertIn('uuid', item)
        self.assertIn('summary', item)
        self.assertIn('user', item)


class TropicalCycloneAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(pk=1, defaults={'maintenance_mode': False})
        user = User.objects.create_user('testuser')
        TropicalCyclone.objects.create(
            user=user, summary='Ciclón activo',
            valid_until=timezone.now() + timedelta(days=1),
        )
        cls.url = reverse('tropical-cyclone-list')

    def test_list_returns_active(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_has_expected_fields(self):
        response = self.client.get(self.url)
        item = response.data[0]
        self.assertIn('uuid', item)
        self.assertIn('date', item)


class StormWarningAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(pk=1, defaults={'maintenance_mode': False})
        user = User.objects.create_user('testuser')
        StormWarning.objects.create(
            user=user, summary='Tormenta activa',
            valid_until=timezone.now() + timedelta(days=1),
        )
        cls.url = reverse('storm-warning-list')

    def test_list_returns_active(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class WeatherReportAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(pk=1, defaults={'maintenance_mode': False})
        cls.user = User.objects.create_user('testuser')
        for rtype in ('today', 'tomorrow', 'commentary', 'note'):
            WeatherReport.objects.create(
                user=cls.user, type=rtype, date=timezone.now(),
                summary=f'Reporte {rtype}',
            )
        cls.valid_url = reverse('weather-report-list', args=['today'])

    def test_valid_type_returns_reports(self):
        response = self.client.get(reverse('weather-report-list', args=['today']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_invalid_type_returns_empty(self):
        url = reverse('weather-report-list', args=['invalid'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_filters_by_type(self):
        today = self.client.get(reverse('weather-report-list', args=['today'])).data
        tomorrow = self.client.get(reverse('weather-report-list', args=['tomorrow'])).data
        self.assertEqual(len(today), 1)
        self.assertEqual(len(tomorrow), 1)
        self.assertEqual(today[0]['type'], 'today')
        self.assertEqual(tomorrow[0]['type'], 'tomorrow')

    def test_has_expected_fields(self):
        response = self.client.get(reverse('weather-report-list', args=['today']))
        item = response.data[0]
        self.assertIn('uuid', item)
        self.assertIn('type', item)
        self.assertIn('summary', item)


class ScientificPublicationAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(pk=1, defaults={'maintenance_mode': False})
        author = Author.objects.create(first_name='John', last_name='Doe')
        pub = ScientificPublication.objects.create(
            title='Test Paper', summary='Abstract',
            publication_date=date.today(), author=author,
        )
        cls.url = reverse('publication-list')

    def test_list_returns_publications(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_has_expected_fields(self):
        response = self.client.get(self.url)
        item = response.data[0]
        self.assertIn('title', item)
        self.assertIn('author', item)
        self.assertIn('publication_date', item)


class ServiceAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(pk=1, defaults={'maintenance_mode': False})
        user = User.objects.create_user('testuser')
        Service.objects.create(
            user=user, title='Gratuito', service_type='public',
            summary='Servicio público',
        )
        Service.objects.create(
            user=user, title='Pago', service_type='commercial',
            summary='Servicio comercial', price=100,
        )
        cls.url = reverse('service-list')

    def test_list_returns_only_public(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_excludes_commercial(self):
        response = self.client.get(self.url)
        titles = [s['title'] for s in response.data]
        self.assertIn('Gratuito', titles)
        self.assertNotIn('Pago', titles)

    def test_has_expected_fields(self):
        response = self.client.get(self.url)
        item = response.data[0]
        self.assertIn('uuid', item)
        self.assertIn('title', item)
        self.assertIn('service_type', item)
