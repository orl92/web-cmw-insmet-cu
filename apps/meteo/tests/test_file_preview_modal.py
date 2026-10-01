"""Verification tests for the meteo warning/weather_report form templates.

Asserts that uploaded PDFs must not open in a blank tab and instead use the
shared ``#documentPdfModal`` (data-pdf-url). Templates are NOT modified.

NOTE: the base layout footer intentionally keeps ``target="_blank"`` on its
social-media links — out of scope — so we assert the *file anchor* does not
use ``target="_blank"`` rather than the whole page.
"""

import io
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from apps.meteo.models import Warning, WeatherReport

User = get_user_model()

PDF_BYTES = b'%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF'


def _png_1x1():
    """Devuelve los bytes de un PNG 1x1 generado por Pillow, no un literal.

    El literal base64 que estaba aca antes estaba corrupto: despues del chunk
    IDAT, el decoder leia una longitud de 2 GiB y un tipo de chunk
    ``b'\x00\x00IE'`` en lugar de IEND. ``Image.open()`` es perezoso y solo lee
    la cabecera, asi que los bytes malos pasaban inadvertidos en los tests que
    solo guardan el archivo. Generar los bytes elimina de raiz la clase de bug
    "alguien tipo mal el base64".
    """
    buffer = io.BytesIO()
    Image.new('RGB', (1, 1), (200, 200, 200)).save(buffer, format='PNG')
    return buffer.getvalue()


PNG_BYTES = _png_1x1()


def assert_file_anchor_not_blank_tab(test_case, content, file_url):
    needle = ('href="' + file_url + '" target="_blank"').encode()
    test_case.assertNotIn(needle, content)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class MeteoFilePreviewModalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin3', 'admin3@example.com', 'pass')
        self.user.first_name = 'Admin'
        self.user.last_name = 'Test'
        self.user.email = 'admin3@example.com'
        self.user.save()

        self.warning = Warning.objects.create(
            warning_type='early',
            summary='Resumen de aviso',
            user=self.user,
            valid_until=timezone.now() + timedelta(days=1),
            file=SimpleUploadedFile('doc.pdf', PDF_BYTES, 'application/pdf'),
        )
        self.report = WeatherReport.objects.create(
            report_type='today',
            summary='Resumen de reporte',
            user=self.user,
            file=SimpleUploadedFile('doc.pdf', PDF_BYTES, 'application/pdf'),
        )

    def test_alerta_temprana_update_no_blank_tab_and_pdf_modal(self):
        self.client.force_login(self.user)
        url = reverse('meteo:alerta_temprana_update', kwargs={'uuid': self.warning.uuid})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'documentPdfModal', resp.content)
        self.assertIn(b'data-pdf-url=', resp.content)
        assert_file_anchor_not_blank_tab(self, resp.content, self.warning.file.url)

    def test_tiempo_hoy_update_no_blank_tab_and_pdf_modal(self):
        self.client.force_login(self.user)
        url = reverse('meteo:tiempo_hoy_update', kwargs={'uuid': self.report.uuid})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'documentPdfModal', resp.content)
        self.assertIn(b'data-pdf-url=', resp.content)
        assert_file_anchor_not_blank_tab(self, resp.content, self.report.file.url)
