from django.test import TestCase

from apps.core.models import FileHandlerMixin, SiteConfiguration


class SiteConfigurationBrandingModelTests(TestCase):
    def test_branding_fields_exist_with_defaults(self):
        site = SiteConfiguration.objects.create(maintenance_mode=False)
        self.assertEqual(site.primary_color, '#0b6e99')
        self.assertEqual(site.theme_base, 'gray')
        self.assertFalse(site.brand_logo)
        self.assertFalse(site.favicon)

    def test_site_configuration_inherits_file_handler_mixin(self):
        self.assertTrue(issubclass(SiteConfiguration, FileHandlerMixin))
        self.assertEqual(SiteConfiguration.file_fields, ['brand_logo', 'favicon'])
