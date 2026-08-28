from unittest.mock import patch

from django.conf import settings
from django.core.cache import caches
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from apps.core.cache_utils import safe_cache_get, safe_cache_set
from apps.core.utils import rate_limit_ip


class SafeCacheDegradationTests(TestCase):
    """CACHE-2: a cache backend failure must degrade, never raise a 500."""

    def test_safe_cache_get_returns_default_on_backend_error(self):
        backend = caches['default']
        with patch.object(backend, 'get', side_effect=ConnectionError('redis down')):
            self.assertEqual(safe_cache_get('missing-key', 'fallback'), 'fallback')

    def test_safe_cache_set_swallows_backend_error(self):
        backend = caches['default']
        with patch.object(backend, 'set', side_effect=ConnectionError('redis down')):
            safe_cache_set('k', 'v', 60)  # must not raise

    def test_safe_cache_roundtrip_when_healthy(self):
        safe_cache_set('healthy:key', 'value', 60)
        self.assertEqual(safe_cache_get('healthy:key'), 'value')


class CacheBackendConfigTests(TestCase):
    """CACHE-1: backend selection is environment-driven with LocMemCache fallback."""

    def test_default_backend_is_locmem_without_redis(self):
        # USE_REDIS_CACHE defaults to False, so the default cache must be the
        # in-process LocMemCache -- dev/CI run with no Redis server.
        self.assertEqual(
            settings.CACHES['default']['BACKEND'],
            'django.core.cache.backends.locmem.LocMemCache',
        )
        self.assertEqual(caches['default'].__class__.__name__, 'LocMemCache')


class RateLimitIpRegressionTests(TestCase):
    """rate_limit_ip must keep working against the (now shared) default cache."""

    def test_rate_limit_blocks_after_threshold(self):
        factory = RequestFactory()

        @rate_limit_ip(limit=2, window=60, key_prefix='test_rl')
        def view(request):
            return HttpResponse('ok')

        ip = '203.0.113.9'
        for _ in range(2):
            req = factory.get('/')
            req.META['REMOTE_ADDR'] = ip
            self.assertEqual(view(req).status_code, 200)
        req = factory.get('/')
        req.META['REMOTE_ADDR'] = ip
        self.assertEqual(view(req).status_code, 429)
