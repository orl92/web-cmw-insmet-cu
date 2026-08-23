"""Accessibility contract tests for the home index UV gauge (015-home-templates-ui, Phase 7).

Task 7.1: the UV index <svg> must expose role="img" plus a descriptive <title>
(and optional <desc>), and the repeated decorative gauge arcs must be
aria-hidden so assistive tech reads only the labeled image, not the gauge chrome.
The SVG only renders when a forecast with a UV index exists, so the suite
creates one.
"""

import re
from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.meteo.models import Forecasts


class IndexUvSvgA11yTests(TestCase):
    """Task 7.1 — pages/home/index.html UV gauge."""

    @classmethod
    def setUpTestData(cls):
        Forecasts.objects.create(
            date=date.today(),
            lp='Luna Llena',
            nlp='Menguante',
            nlpd=date.today(),
            sunrise='06:00:00',
            sunset='18:00:00',
            uv_index=7,
        )

    def setUp(self):
        self.html = self.client.get(reverse('home:index')).content.decode()

    @staticmethod
    def _uv_svg(html):
        """Return the UV gauge <svg ...>...</svg> block, or None."""
        match = re.search(
            r'<svg\b[^>]*aria-labelledby="uv-svg-title[^"]*"[^>]*>.*?</svg>',
            html,
            flags=re.DOTALL,
        )
        return match.group(0) if match else None

    def test_uv_svg_carries_role_img(self):
        svg = self._uv_svg(self.html)
        self.assertIsNotNone(svg, msg='UV gauge <svg> not found')
        self.assertIn('role="img"', svg)

    def test_uv_svg_carries_title(self):
        svg = self._uv_svg(self.html)
        self.assertIsNotNone(svg, msg='UV gauge <svg> not found')
        self.assertIn('<title', svg)
        # The title must convey the UV value rendered from the context.
        self.assertIn('Índice UV', svg)

    def test_uv_svg_decorative_arcs_are_aria_hidden(self):
        svg = self._uv_svg(self.html)
        self.assertIsNotNone(svg, msg='UV gauge <svg> not found')
        paths = re.findall(r'<path\b', svg)
        self.assertEqual(6, len(paths), msg='expected 6 decorative gauge arcs')
        self.assertEqual(
            6,
            svg.count('aria-hidden="true"'),
            msg='all 6 decorative arcs must be aria-hidden',
        )
