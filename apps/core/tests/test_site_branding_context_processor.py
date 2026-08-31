from django.test import RequestFactory, TestCase

from apps.core.context_processors import site_branding
from apps.core.models import SiteConfiguration


class SiteBrandingContextProcessorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_returns_existing_site_configuration_singleton(self):
        site = SiteConfiguration.objects.create(maintenance_mode=False)
        request = self.factory.get('/')
        context = site_branding(request)
        self.assertEqual(context['site_branding'].pk, site.pk)
        self.assertEqual(context['site_branding'].maintenance_mode, False)

    def test_creates_singleton_when_no_row_exists(self):
        SiteConfiguration.objects.all().delete()
        request = self.factory.get('/')
        context = site_branding(request)
        self.assertIsInstance(context['site_branding'], SiteConfiguration)
        self.assertEqual(SiteConfiguration.objects.count(), 1)
