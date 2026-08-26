"""UI contract tests for the shared document card + PDF modal (016-public-ui-ux, Phase 1).

The card MUST use a <button> modal trigger (never href="#") carrying data-pdf-url,
and the shared modal MUST render a native <object type="application/pdf"> plus a
download <a download> fallback.
"""

from django.template.loader import render_to_string
from django.test import TestCase


class DocumentCardModalTests(TestCase):
    def test_card_renders_button_with_pdf_url_not_href(self):
        html = render_to_string(
            'includes/home/document_card.html',
            {
                'title': 'Pronóstico del Tiempo',
                'summary': 'Resumen',
                'publisher': 'Autor',
                'date': '05/08/2026',
                'pdf_url': '/media/pronostico.pdf',
                'pdf_title': 'Pronóstico',
            },
        )
        self.assertIn('<button type="button"', html)
        self.assertIn('data-pdf-url="/media/pronostico.pdf"', html)
        self.assertIn('data-bs-target="#documentPdfModal"', html)
        self.assertNotIn('href="#"', html)

    def test_modal_renders_object_and_download_fallback(self):
        html = render_to_string('includes/home/document_pdf_modal.html')
        # djlint may wrap long attribute lists across lines; match across them.
        self.assertRegex(html, r'<object id="documentPdfObject"[^>]*type="application/pdf"')
        self.assertRegex(html, r'<a id="documentPdfDownload"[^>]*download')
        self.assertIn('aria-label="Cerrar"', html)
