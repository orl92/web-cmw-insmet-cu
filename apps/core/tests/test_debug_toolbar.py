import os

from django.conf import settings
from django.test import TestCase


class DebugToolbarSettingsTestCase(TestCase):
    def test_debug_toolbar_guard(self):
        import debug_toolbar

        self.assertTrue(hasattr(debug_toolbar, 'VERSION'))

        if 'PRODUCTION' in os.environ:
            self.skipTest('IS_PRODUCTION=True: toolbar must stay inert in production')

        expected = os.getenv('DEBUG', 'False') == 'True' and 'PRODUCTION' not in os.environ
        if expected:
            self.assertIn('debug_toolbar', settings.INSTALLED_APPS)
            self.assertIn(
                'debug_toolbar.middleware.DebugToolbarMiddleware',
                settings.MIDDLEWARE,
            )
        else:
            self.assertNotIn('debug_toolbar', settings.INSTALLED_APPS)
