"""Accessibility contract tests for the satellite gallery (015-home-templates-ui, Phase 6).

Task 6.1: both satellite gallery anchor groups must expose role="img" and an
accessible name via aria-label (the caption text that used to render visibly), and
the decorative background-image <div> inside each anchor must be aria-hidden.
"""

import re

from django.test import TestCase
from django.urls import reverse

# Anchor hrefs that identify each gallery group.
FSLIGHTBOX_HREFS = [
    '/proxy_image/?image_path=real-time/sal/g16split/g16split.jpg',
    '/proxy_image/?image_path=real-time/sal/g16natcol/g16nc.jpg',
    '/proxy_image/?image_path=real-time/sal/g16wvupper/g16wvupper.jpg',
    '/proxy_image/?image_path=real-time/sal/g16wvmid/g16wvmid.jpg',
    '/proxy_image/?image_path=real-time/sal/g16wvlow/g16wvlow.jpg',
]
EXTERNAL_HREFS = [
    'https://weather.ndc.nasa.gov/goes/abi/goesEastconusband02.html',
    'https://weather.ndc.nasa.gov/goes/abi/goesEastconusband13.html',
    'https://www.star.nesdis.noaa.gov/goes/sector.php?sat=G16&sector=car',
]

# Caption text moved from the visible <small> into each anchor's aria-label.
EXPECTED_LABELS = {
    FSLIGHTBOX_HREFS[0]: 'Polvo',
    FSLIGHTBOX_HREFS[1]: 'Color Natural',
    FSLIGHTBOX_HREFS[2]: 'Vapor de agua niveles altos',
    FSLIGHTBOX_HREFS[3]: 'Vapor de agua niveles medios',
    FSLIGHTBOX_HREFS[4]: 'Vapor de agua niveles bajos',
    EXTERNAL_HREFS[0]: 'Nubes diurnas, niebla, insolación, vientos.',
    EXTERNAL_HREFS[1]: 'Temperatura superficial y nubes.',
    EXTERNAL_HREFS[2]: 'Imagenes del Sector: Caribe -NOAA / NESDIS /STAR',
}


class SatelliteGalleryA11yTests(TestCase):
    """Task 6.1 — pages/home/satellites/satellites.html."""

    def setUp(self):
        self.html = self.client.get(reverse('home:satellite')).content.decode()

    @staticmethod
    def _anchor_tag(html, href):
        """Return the opening <a ...> tag for a given href, or None."""
        pattern = re.compile(rf'<a\b[^>]*href="{re.escape(href)}"[^>]*>')
        match = pattern.search(html)
        return match.group(0) if match else None

    def test_every_gallery_anchor_carries_role_img(self):
        for href in FSLIGHTBOX_HREFS + EXTERNAL_HREFS:
            with self.subTest(href=href):
                tag = self._anchor_tag(self.html, href)
                self.assertIsNotNone(tag, msg=f'anchor for {href} not found')
                self.assertIn('role="img"', tag)

    def test_every_gallery_anchor_carries_aria_label(self):
        for href, label in EXPECTED_LABELS.items():
            with self.subTest(href=href, label=label):
                tag = self._anchor_tag(self.html, href)
                self.assertIsNotNone(tag, msg=f'anchor for {href} not found')
                self.assertIn(f'aria-label="{label}"', tag)

    def test_decorative_background_divs_are_aria_hidden(self):
        # Each gallery anchor wraps exactly one aria-hidden background-image div.
        anchor_blocks = re.findall(r'<a\b[^>]*>.*?</a>', self.html, flags=re.DOTALL)
        gallery_blocks = [
            block
            for block in anchor_blocks
            if any(href in block for href in FSLIGHTBOX_HREFS + EXTERNAL_HREFS)
        ]
        self.assertEqual(8, len(gallery_blocks))
        for block in gallery_blocks:
            self.assertIn('aria-hidden="true"', block)

    def test_visible_caption_text_was_moved_to_aria_label(self):
        # The old visible captions are gone; their text now lives in aria-label.
        visible_captions = [
            'text-secondary">Polvo',
            'text-secondary">Color Natural',
            'text-secondary">Vapor de agua niveles altos',
            'text-secondary">Vapor de agua niveles medios',
            'text-secondary">Vapor de agua niveles bajos',
        ]
        for visible in visible_captions:
            self.assertNotIn(visible, self.html)
