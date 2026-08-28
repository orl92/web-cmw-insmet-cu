from unittest.mock import patch

from django.core.cache import cache
from django.core.cache.backends.locmem import LocMemCache
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.core.cache_utils import build_api_cache_key
from apps.core.models import SiteConfiguration
from apps.meteo.models import Province, Station


class FailingCacheBackend(LocMemCache):
    """Simulates Redis being unreachable while USE_REDIS_CACHE=True."""

    def get(self, key, default=None, version=None, client=None):
        raise ConnectionError('redis down')

    def set(self, key, value, timeout=0, version=None, client=None, **kwargs):
        raise ConnectionError('redis down')


class StationListCacheTests(APITestCase):
    """CACHE-4: public list endpoints are cached by path + query string."""

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        prov = Province.objects.create(name='Camaguey', code='CM')
        Station.objects.create(name='A', number=1, province=prov, latitude=1, longitude=1)
        Station.objects.create(name='B', number=2, province=prov, latitude=1, longitude=1)
        cls.url = reverse('station-list')

    def setUp(self):
        cache.clear()

    def test_cache_hit_serves_stale_data_after_db_wipe(self):
        r1 = self.client.get(self.url)
        self.assertEqual(r1.status_code, 200)
        self.assertIsNotNone(cache.get(build_api_cache_key(r1.wsgi_request)))
        # Wipe the DB; a second identical request must be served from cache.
        Station.objects.all().delete()
        r2 = self.client.get(self.url)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual([s['name'] for s in r1.data], [s['name'] for s in r2.data])

    def test_distinct_query_params_produce_distinct_keys(self):
        from django.test import RequestFactory

        req1 = RequestFactory().get('/api/stations/?province=1')
        req2 = RequestFactory().get('/api/stations/?province=2')
        self.assertNotEqual(build_api_cache_key(req1), build_api_cache_key(req2))
        # Both endpoints are cached under their own key.
        self.client.get(self.url + '?province=1')
        self.client.get(self.url + '?province=2')
        self.assertIsNotNone(cache.get(build_api_cache_key(req1)))
        self.assertIsNotNone(cache.get(build_api_cache_key(req2)))

    def test_query_param_order_is_normalized(self):
        from django.test import RequestFactory

        req_a = RequestFactory().get('/api/stations/?a=1&b=2')
        req_b = RequestFactory().get('/api/stations/?b=2&a=1')
        self.assertEqual(build_api_cache_key(req_a), build_api_cache_key(req_b))

    def test_volatile_warning_endpoint_uses_60s_timeout(self):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        with patch('apps.api.views.safe_cache_set') as mock_set:
            self.client.get(reverse('early-warning-list'))
        timeout = mock_set.call_args.args[-1]
        self.assertEqual(timeout, 60)

    def test_stable_station_endpoint_uses_300s_timeout(self):
        with patch('apps.api.views.safe_cache_set') as mock_set:
            self.client.get(self.url)
        timeout = mock_set.call_args.args[-1]
        self.assertEqual(timeout, 300)


class ApiCacheResilienceTests(APITestCase):
    """CACHE-2: Redis down while enabled must not produce a 500."""

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        prov = Province.objects.create(name='Camaguey', code='CM')
        Station.objects.create(name='A', number=1, province=prov, latitude=1, longitude=1)
        Station.objects.create(name='B', number=2, province=prov, latitude=1, longitude=1)
        cls.url = reverse('station-list')

    def test_view_degrades_to_uncached_when_backend_unreachable(self):
        failing = FailingCacheBackend('', {})
        with patch('apps.core.cache_utils.cache', failing):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
