"""Tests de configuración de producción (feature 089)."""

import os
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory, TestCase, override_settings

from config import settings
from config.settings import get_database_config


class ProxyHeaderTests(TestCase):
    """Django debe resolver is_secure() tras el proxy vía X-Forwarded-Proto."""

    def test_is_secure_with_x_forwarded_proto(self):
        factory = RequestFactory()
        request = factory.get('/', HTTP_X_FORWARDED_PROTO='https')
        with override_settings(SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')):
            self.assertTrue(request.is_secure())

    def test_is_secure_without_header(self):
        factory = RequestFactory()
        request = factory.get('/')
        with override_settings(SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')):
            self.assertFalse(request.is_secure())


class DatabaseConfigTests(TestCase):
    """Fail-closed en producción y fallback a SQLite en desarrollo."""

    @mock.patch.dict(os.environ, {}, clear=True)
    @mock.patch.object(settings, 'DEBUG', False)
    @mock.patch.object(settings, 'IS_PRODUCTION', True)
    def test_fail_closed_production_without_db_engine(self):
        with self.assertRaises(ImproperlyConfigured):
            get_database_config()

    @mock.patch.dict(os.environ, {}, clear=True)
    @mock.patch.object(settings, 'DEBUG', False)
    @mock.patch.object(settings, 'IS_PRODUCTION', False)
    def test_dev_fallback_sqlite(self):
        config = get_database_config()
        self.assertEqual(config['default']['ENGINE'], 'django.db.backends.sqlite3')

    @mock.patch.dict(
        os.environ,
        {
            'DB_ENGINE': 'postgresql',
            'DB_NAME': 'x',
            'DB_USER': 'u',
            'DB_HOST': 'h',
            'DB_PASS': 'p',
        },
        clear=True,
    )
    @mock.patch.object(settings, 'DEBUG', False)
    @mock.patch.object(settings, 'IS_PRODUCTION', True)
    def test_prod_with_complete_vars(self):
        config = get_database_config()
        self.assertEqual(config['default']['ENGINE'], 'django.db.backends.postgresql')
