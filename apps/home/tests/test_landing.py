"""023-landing-page — PR1 socials footer contract (task 5.6).

RED-first tests for the vendored Tabler socials plugin (SOCIALS-PLUGIN delta):
the public home footer and the dashboard footer each expose exactly four
`social social-app-{facebook,instagram,x,telegram} social-gray` anchors with
brand aria-labels; head.html links tabler-socials.min.css?v=151 with no CDN;
and every referenced SVG asset resolves locally.
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

BRANDS = ('facebook', 'instagram', 'x', 'telegram')
LABELS = ('Facebook', 'Instagram', 'X', 'Telegram')
ANCHOR_PREFIX = '<a class="social social-app-'
ANCHOR_SUFFIX = ' social-gray"'


class LandingFooterSocialTests(TestCase):
    """Tasks 2.1-2.3 + 5.6 — socials plugin activation contract."""

    def setUp(self):
        self.public = self.client.get(reverse('home:index')).content.decode()
        staff = User.objects.create_user(
            username='staff-socials',
            email='staff@cmw.insmet.cu',
            first_name='Staff',
            last_name='Social',
            is_staff=True,
        )
        self.client.force_login(staff)
        self.dashboard = self.client.get(reverse('dashboard:index')).content.decode()

    @staticmethod
    def _social_count(html):
        return sum(html.count(ANCHOR_PREFIX + brand + ANCHOR_SUFFIX) for brand in BRANDS)

    def test_public_footer_exposes_four_social_gray_anchors(self):
        self.assertEqual(4, self._social_count(self.public))

    def test_dashboard_footer_exposes_four_social_gray_anchors(self):
        self.assertEqual(4, self._social_count(self.dashboard))

    def test_social_anchors_carry_brand_aria_labels(self):
        for brand, label in zip(BRANDS, LABELS, strict=True):
            self.assertIn(ANCHOR_PREFIX + brand + ANCHOR_SUFFIX, self.public, msg=brand)
            self.assertIn(ANCHOR_PREFIX + brand + ANCHOR_SUFFIX, self.dashboard, msg=brand)
            self.assertIn(f'aria-label="{label}"', self.public, msg=label)
            self.assertIn(f'aria-label="{label}"', self.dashboard, msg=label)

    def test_socials_stylesheet_linked_site_wide(self):
        for page in (self.public, self.dashboard):
            self.assertIn('dist/css/tabler-socials.min.css?v=151', page)

    def test_socials_stylesheet_not_served_from_cdn(self):
        for page in (self.public, self.dashboard):
            self.assertNotIn('cdn.jsdelivr.net', page, msg='CDN leak in rendered page')
            self.assertNotIn('unpkg.com', page)

    def test_social_assets_resolve(self):
        social_dir = settings.BASE_DIR / 'static' / 'dist' / 'img' / 'social'
        for brand in BRANDS:
            for asset in (f'{brand}.svg', f'{brand}-gray.svg'):
                self.assertTrue((social_dir / asset).is_file(), msg=asset)

    def test_html_lang_and_theme_attrs(self):
        for page in (self.public, self.dashboard):
            self.assertIn('<html lang="es" data-bs-theme="light"', page)
