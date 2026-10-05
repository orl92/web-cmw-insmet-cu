from unittest.mock import patch

from django.conf import settings
from django.core.cache import caches
from django.core.cache.backends.redis import RedisCache
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from apps.core.cache_utils import safe_cache_get, safe_cache_set
from apps.core.utils import rate_limit_ip
from config.settings import build_caches


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

    def test_safe_cache_get_degrades_when_driver_package_missing(self):
        # `redis` ships in prod.txt only, so USE_REDIS_CACHE=True on a box
        # without it raises ModuleNotFoundError at the first cache call. That
        # is an ImportError, not an OSError: if the wrappers only caught the
        # latter, a dev asking for Redis would get a 500 instead of a cache miss.
        missing = ModuleNotFoundError("No module named 'redis'")
        backend = caches['default']
        with patch.object(backend, 'get', side_effect=missing):
            self.assertEqual(safe_cache_get('missing-key', 'fallback'), 'fallback')

    def test_safe_cache_set_swallows_missing_driver(self):
        missing = ModuleNotFoundError("No module named 'redis'")
        backend = caches['default']
        with patch.object(backend, 'set', side_effect=missing):
            safe_cache_set('k', 'v', 60)  # must not raise


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

    def test_build_caches_selects_redis_when_enabled(self):
        # Positive branch (CACHE-1): USE_REDIS_CACHE=True must yield RedisCache
        # as the selected backend, driven by the REDIS_URL argument.
        config = build_caches(True, 'redis://127.0.0.1:6379/1')
        self.assertEqual(
            config['default']['BACKEND'],
            'django.core.cache.backends.redis.RedisCache',
        )
        self.assertEqual(config['default']['LOCATION'], 'redis://127.0.0.1:6379/1')

    def test_redis_backend_instantiates_lazily_without_live_server(self):
        # The selected RedisCache must be instantiable WITHOUT a running Redis.
        # Django's RedisCache is lazy: it only parses the URL and imports redis
        # at construction, deferring the real connection until first use.
        with override_settings(CACHES=build_caches(True, 'redis://127.0.0.1:6379/1')):
            backend = caches['default']
            self.assertIsInstance(backend, RedisCache)
            # Laziness proof: client not opened until a command touches Redis.
            self.assertIsNone(getattr(backend, '_client', None))


class RateLimitIpRegressionTests(TestCase):
    """rate_limit_ip must keep working against the shared default cache."""

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
