from django.conf import settings
from django.test import TestCase
from django.urls import NoReverseMatch, reverse


class DebugToolbarInertnessTestCase(TestCase):
    """django-debug-toolbar must be active ONLY in dev (DEBUG and not IS_PRODUCTION).

    The guard decision is captured once at import time in
    ``settings.DEBUG_TOOLBAR_ENABLED`` (NOT re-read from ``settings.DEBUG`` at
    request time, because Django's test runner forces ``settings.DEBUG = False``
    after import). Tests assert the toolbar's *side effects* (INSTALLED_APPS and
    URL routes) follow that flag, so a regression that leaks the toolbar into
    production fails closed in CI instead of being skipped.
    """

    def test_package_installed(self):
        # Required by requirements/test.txt (and dev.txt); if missing the app would fail to load.
        import debug_toolbar

        self.assertTrue(hasattr(debug_toolbar, 'VERSION'))

    def test_toolbar_enabled_iff_guard_flag(self):
        self.assertEqual(
            'debug_toolbar' in settings.INSTALLED_APPS,
            settings.DEBUG_TOOLBAR_ENABLED,
        )

    def test_toolbar_routes_match_enabled_state(self):
        if settings.DEBUG_TOOLBAR_ENABLED:
            url = reverse('djdt:render_panel')
            self.assertIn('/__debug__/', url)
        else:
            with self.assertRaises(NoReverseMatch):
                reverse('djdt:render_panel')
