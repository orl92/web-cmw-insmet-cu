"""Tabler 1.5.1 vendor contracts (tabler-core-vendor + tema-personalizado).

Contracts the vendored assets must satisfy:
- LIGHT-DEFAULT-EXPLICIT: home and dashboard render ``<html data-bs-theme="light">``
  server-side; head.html pre-paint always sets the attribute; the vendored
  assets are cache-busted with ``?v=151``.
- NO-CDN-NO-BUILD: no cdn.jsdelivr.net / unpkg.com reference in templates or
  in the vendored Tabler assets.
- UMD-EXPOSURE-CONTRACT: maps.js builds its toast through the
  ``(window.tabler && window.tabler.bootstrap) || window.bootstrap`` fallback
  and uses Tabler webfont icons (``ti ti-*``), never FontAwesome (``fas fa-*``).
"""

from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.core.models import SiteConfiguration

BASE_DIR = Path(settings.BASE_DIR)

# ?v=151 cache busting on the 4 vendored assets (3 CSS in head.html, 1 JS in
# scripts.html). Order matters: [0:3] are the head.html stylesheet links.
SWAPPED_CACHE_BUSTED_LINKS = [
    'dist/css/tabler.min.css?v=151',
    'dist/css/tabler-themes.min.css?v=151',
    'dist/css/tabler-icons.min.css?v=151',
    'dist/js/tabler.min.js?v=151',
]

TABLER_ASSETS = [
    'static/dist/css/tabler.min.css',
    'static/dist/css/tabler-themes.min.css',
    'static/dist/css/tabler-icons.min.css',
    'static/dist/css/tabler-socials.min.css',
    'static/dist/js/tabler.min.js',
    'static/dist/js/tabler-theme.min.js',
]


class Tabler151UpgradeRenderTests(TestCase):
    """Rendered HTML carries the explicit light default and cache-busted links."""

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        cls.user = User.objects.create_superuser(
            'tabler_admin',
            'tabler_admin@example.com',
            'password',
            first_name='Tabler',
            last_name='Admin',
        )

    def test_home_page_renders_explicit_light_theme(self):
        response = self.client.get(reverse('home:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<html lang="es" data-bs-theme="light">', count=1)
        self.assertNotContains(response, 'data-bs-theme="auto"')

    def test_dashboard_renders_explicit_light_theme(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<html lang="es" data-bs-theme="light" data-bs-navbar-position="vertical">',
            count=1,
        )
        self.assertNotContains(response, 'data-bs-theme="auto"')

    def test_home_page_cache_busts_all_four_swapped_assets(self):
        response = self.client.get(reverse('home:index'))
        self.assertEqual(response.status_code, 200)
        for link in SWAPPED_CACHE_BUSTED_LINKS:
            self.assertContains(response, link, msg_prefix=link)

    def test_home_page_injects_model_theme_config_server_side(self):
        # THEME-BASE-APPLIED: the pre-paint inline model block carries the
        # SiteConfiguration values rendered server-side (theme_base/font/radius/
        # primary), so data-bs-theme-base/--tblr-primary come from the model on
        # load, not from a documented default. Prove it with non-default values.
        site = SiteConfiguration.objects.first()
        site.theme_base = 'zinc'
        site.theme_font = 'serif'
        site.primary_color = 'red'
        site.save(update_fields=['theme_base', 'theme_font', 'primary_color'])
        response = self.client.get(reverse('home:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"theme-base": "zinc"')
        self.assertContains(response, '"theme-font": "serif"')
        self.assertContains(response, '"theme-primary": "red"')


class Tabler151UpgradeFileContractTests(TestCase):
    """Source-level contracts: pre-paint script, layouts, maps.js, CDN absence."""

    @staticmethod
    def _read(rel_path):
        return (BASE_DIR / rel_path).read_text(encoding='utf-8')

    def test_head_html_prepaint_sets_theme_attribute_always(self):
        head = self._read('templates/includes/base/head.html')
        self.assertIn('setAttribute("data-bs-theme", theme)', head)
        self.assertNotIn('removeAttribute("data-bs-theme")', head)

    def test_head_html_cache_busts_three_swapped_css(self):
        head = self._read('templates/includes/base/head.html')
        for link in SWAPPED_CACHE_BUSTED_LINKS[:3]:
            self.assertIn(link, head, msg=link)

    def test_scripts_html_cache_busts_swapped_js(self):
        scripts = self._read('templates/includes/base/scripts.html')
        self.assertIn(SWAPPED_CACHE_BUSTED_LINKS[3], scripts)

    def test_layouts_carry_static_light_theme_attribute(self):
        for layout in ('templates/layouts/base.html', 'templates/layouts/base-auth.html'):
            self.assertIn('lang="es" data-bs-theme="light"', self._read(layout))

    def test_dashboard_layout_declares_vertical_navbar_position(self):
        # Tabler 1.5.1 hides .navbar-vertical when .page contains a horizontal
        # navbar and <html> lacks data-bs-navbar-position="vertical". The CMP
        # dashboard keeps BOTH navbars, so the vertical position is the default
        # declared by base.html; the public home layout blanks the block.
        base = self._read('templates/layouts/base.html')
        self.assertIn('data-bs-navbar-position="vertical"', base)
        self.assertIn(
            '{% block html_attrs %}{% endblock %}', self._read('templates/layouts/home.html')
        )

    def test_layouts_header_comment_bumped_to_151(self):
        for layout in ('templates/layouts/base.html', 'templates/layouts/base-auth.html'):
            self.assertIn('@version 1.5.1', self._read(layout))

    def test_maps_js_uses_tabler_bootstrap_fallback(self):
        maps = self._read('static/dist/js/maps.js')
        self.assertIn('(window.tabler && window.tabler.bootstrap) || window.bootstrap', maps)
        self.assertIn('new Bootstrap.Toast(', maps)
        self.assertNotIn('new bootstrap.Toast(', maps)

    def test_maps_js_toast_uses_tabler_webfont_icons(self):
        maps = self._read('static/dist/js/maps.js')
        for icon in ('ti ti-circle-check', 'ti ti-alert-triangle', 'ti ti-info-circle'):
            self.assertIn(icon, maps, msg=icon)
        self.assertNotRegex(maps, r'fas\s+fa-')

    def test_no_cdn_references_in_templates(self):
        scanned = 0
        for path in (BASE_DIR / 'templates').rglob('*'):
            if not path.is_file() or path.suffix not in {'.html', '.js', '.css', '.txt', '.svg'}:
                continue
            scanned += 1
            content = path.read_text(encoding='utf-8', errors='ignore')
            self.assertNotIn('cdn.jsdelivr.net', content, msg=str(path))
            self.assertNotIn('unpkg.com', content, msg=str(path))
        # Prove the loop really walked the tree (ghost-loop guard).
        self.assertGreater(scanned, 50)

    def test_no_cdn_references_in_vendored_tabler_assets(self):
        for rel in TABLER_ASSETS:
            content = self._read(rel)
            self.assertNotIn('cdn.jsdelivr.net', content, msg=rel)
            self.assertNotIn('unpkg.com', content, msg=rel)

    def test_webfont_icons_scaled_via_icon_size_variable_not_font_size(self):
        # Tabler 1.5.1 .icon uses display:inline-block with a fixed
        # width/height box driven by --tblr-icon-size (default 1.25rem). An
        # inline `font-size` on the glyph grows it beyond that box, so the
        # icon overflows its card/footer/empty-state container (dashboard KPI
        # cards, comercial cards, footer social icons, pdf avatar placeholder,
        # toast/station icons built in project JS).
        # Scale the icon the canonical way: --tblr-icon-size: <size>.
        import re

        scanned = 0
        roots = (
            (BASE_DIR / 'templates', {'.html'}),
            (BASE_DIR / 'apps', {'.html'}),
            (BASE_DIR / 'static' / 'dist' / 'js', {'.js'}),
        )
        for root, suffixes in roots:
            for path in root.rglob('*'):
                if not path.is_file() or path.suffix not in suffixes:
                    continue
                if path.name.endswith('.min.js'):
                    continue
                scanned += 1
                content = path.read_text(encoding='utf-8', errors='ignore')
                if re.search(r'class="icon ti.{0,120}?font-size:', content, re.DOTALL):
                    self.fail(f'{path}: webfont icon scaled with inline font-size')
        self.assertGreater(scanned, 20)
