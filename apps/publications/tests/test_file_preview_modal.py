"""Verification tests for the publications update form template.

Asserts that the PDF no longer opens in a blank tab and instead uses the
shared ``#documentPdfModal`` (data-pdf-url). Templates are NOT modified.

NOTE: the base layout footer intentionally keeps ``target="_blank"`` on its
social-media links — out of scope — so we assert the *file anchor* does not
use ``target="_blank"`` rather than the whole page.
"""

import base64
import tempfile
from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.publications.models import Author, ScientificPublication

User = get_user_model()

PDF_BYTES = b'%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF'
PNG_BYTES = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
)


def assert_file_anchor_not_blank_tab(test_case, content, file_url):
    needle = ('href="' + file_url + '" target="_blank"').encode()
    test_case.assertNotIn(needle, content)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PublicationsFilePreviewModalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin2', 'admin2@example.com', 'pass')
        self.user.first_name = 'Admin'
        self.user.last_name = 'Test'
        self.user.email = 'admin2@example.com'
        self.user.save()

        self.author = Author.objects.create(first_name='Autor', last_name='Uno')
        self.publication = ScientificPublication.objects.create(
            title='Publicacion de prueba',
            author=self.author,
            publication_date=date(2024, 1, 1),
            summary='Resumen de prueba',
            pdf=SimpleUploadedFile('doc.pdf', PDF_BYTES, 'application/pdf'),
        )

    def test_update_no_blank_tab_and_pdf_modal(self):
        self.client.force_login(self.user)
        url = reverse('publications:update', kwargs={'uuid': self.publication.uuid})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'documentPdfModal', resp.content)
        self.assertIn(b'data-pdf-url=', resp.content)
        assert_file_anchor_not_blank_tab(self, resp.content, self.publication.pdf.url)
