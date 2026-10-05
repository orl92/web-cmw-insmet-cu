"""Tests for global DRF pagination (change 010-api-pagination).

Asserts the paginated envelope on list endpoints, the station exemption as a
flat array, the forecast detail single-object shape, and the drf-spectacular
OpenAPI schema documenting the envelope.
"""

import json
from datetime import date, time, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.commercial.models import Service
from apps.core.models import SiteConfiguration
from apps.meteo.models import Forecasts, Station
from apps.meteo.models import Warning as MeteoWarning


class PaginationSettingsTests(APITestCase):
    """Requirement: Global DRF pagination configuration."""

    def test_default_pagination_class_is_set(self):
        self.assertEqual(
            settings.REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS'],
            'rest_framework.pagination.PageNumberPagination',
        )

    def test_page_size_is_50(self):
        self.assertEqual(settings.REST_FRAMEWORK['PAGE_SIZE'], 50)


class StationListUnpaginatedTests(APITestCase):
    """Requirement: Station list stays a flat array for map_station.js."""

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        Station.objects.create(name='Florida', number=78350, latitude=21.5, longitude=-78.2)
        Station.objects.create(name='Camagüey', number=78355, latitude=21.4, longitude=-77.9)
        cls.url = '/api/stations/'

    def test_stations_is_flat_array(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        # Triangulation: the flat array contains the real seeded stations.
        names = [s['name'] for s in response.data]
        self.assertIn('Florida', names)
        self.assertIn('Camagüey', names)

    def test_stations_has_no_envelope_keys(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ('results', 'count', 'next', 'previous'):
            self.assertNotIn(key, response.data)


class EarlyWarningPaginatedTests(APITestCase):
    """Requirement: affected list endpoint returns {count,next,previous,results}."""

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        user = User.objects.create_user('wuser')
        for i in range(60):
            MeteoWarning.objects.create(
                user=user,
                warning_type='early',
                summary=f'early-{i}',
                valid_until=timezone.now() + timedelta(days=1),
            )
        cls.url = '/api/early-warnings/'

    def test_page1_envelope_and_size(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ('count', 'next', 'previous', 'results'):
            self.assertIn(key, response.data)
        # count reflects ALL active early warnings, not just page 1.
        self.assertEqual(response.data['count'], 60)
        self.assertLessEqual(len(response.data['results']), 50)
        self.assertEqual(len(response.data['results']), 50)
        self.assertIsNone(response.data['previous'])
        self.assertIsNotNone(response.data['next'])

    def test_page2_is_reachable_and_different_slice(self):
        page1 = self.client.get(self.url).data
        page2 = self.client.get(self.url, {'page': 2}).data
        self.assertIsNotNone(page2['previous'])
        first_p1 = page1['results'][0]['uuid']
        first_p2 = page2['results'][0]['uuid']
        # Triangulation: different slice, not the same page repeated.
        self.assertNotEqual(first_p1, first_p2)
        self.assertEqual(len(page2['results']), 10)


class ForecastDetailNotPaginatedTests(APITestCase):
    """Requirement: detail endpoint returns a single object, not paginated."""

    @classmethod
    def setUpTestData(cls):
        from apps.meteo.models import ForecastRegions

        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        today = date.today()
        forecast = Forecasts.objects.create(
            date=today,
            lp='Luna Nueva',
            nlp='Cuarto Creciente',
            nlpd=today + timedelta(days=7),
            sunrise=time(6, 30),
            sunset=time(18, 30),
            uv_index=5,
        )
        ForecastRegions.objects.create(
            forecast=forecast,
            region='north',
            period='morning',
            temp=25,
            weather='PN',
            wind_dir='N',
            wind_speed='10',
        )
        cls.url = f'/api/forecast/{today.isoformat()}/'

    def test_forecast_returns_single_object(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertNotIn('results', response.data)
        # Triangulation: it is the actual forecast, not an empty wrapper.
        self.assertIn('north', response.data)
        self.assertIn('interior', response.data)


class OpenAPISchemaPaginationTests(APITestCase):
    """Requirement: drf-spectacular documents the paginated envelope."""

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})

    def test_schema_documents_paginated_envelope(self):
        response = self.client.get('/api/schema/?format=json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schema = json.loads(response.content)
        # Early-warnings response schema references the PaginatedWarningList.
        ew = schema['paths']['/api/early-warnings/']['get']['responses']['200']
        content = ew['content']['application/json']['schema']
        self.assertIn('$ref', content)
        ref = content['$ref'].split('/')[-1]
        component = schema['components']['schemas'][ref]
        for key in ('count', 'next', 'previous', 'results'):
            self.assertIn(key, component['properties'])

    def test_schema_documents_stations_as_plain_array(self):
        response = self.client.get('/api/schema/?format=json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schema = json.loads(response.content)
        stations = schema['paths']['/api/stations/']['get']['responses']['200']
        content = stations['content']['application/json']['schema']
        # Plain array, not a paginated envelope object.
        self.assertEqual(content['type'], 'array')
        self.assertIn('$ref', content['items'])
        self.assertNotIn('results', content)
        self.assertNotIn('count', content)


class PublicServicesOrderedTests(APITestCase):
    """Requirement: the public services list is ordered newest-first.

    `.order_by('-date')` on the Service queryset is what keeps
    ``UnorderedObjectListWarning`` from being raised.
    """

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        cls.user = User.objects.create_user('svcuser')
        cls.url = '/api/services/'

    def setUp(self):
        # CacheAPIMixin cachea /api/services/ 300s y el cache locMem persiste
        # entre métodos del mismo TestCase; lo limpiamos para isolación real.
        cache.clear()

    def _create_service(self, title, age_days):
        service = Service.objects.create(
            user=self.user,
            title=title,
            summary=f'Resumen de {title}',
            service_type='public',
        )
        # auto_now_add no puede fijarse a mano; lo respaldamos con update()
        # para forzar fechas distintas y un orden determinista.
        Service.objects.filter(pk=service.pk).update(date=timezone.now() - timedelta(days=age_days))
        return service

    def test_services_are_ordered_newest_first(self):
        self._create_service('Servicio Viejo', age_days=10)
        self._create_service('Servicio Medio', age_days=5)
        self._create_service('Servicio Nuevo', age_days=0)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [item['title'] for item in response.data['results']]
        self.assertEqual(titles, ['Servicio Nuevo', 'Servicio Medio', 'Servicio Viejo'])

    def test_services_paginated_envelope(self):
        self._create_service('Único Servicio', age_days=0)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ('count', 'next', 'previous', 'results'):
            self.assertIn(key, response.data)
        self.assertEqual(response.data['count'], 1)
