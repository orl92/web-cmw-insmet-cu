"""Verification tests for the dashboard "edit/create" form templates.

These tests assert that uploaded files must not open in a blank browser tab
(``target="_blank"`` on the file anchor) and instead rely on the shared
``#documentPdfModal`` for PDFs and the vendored fslightbox for images.
Templates are NOT modified; we only assert on rendered output.

NOTE: the base layout footer intentionally keeps ``target="_blank"`` on its
social-media links (Instagram/Facebook/X/Telegram) — that is out of scope and
unrelated to the file preview, so we assert the *file anchor* does not
use ``target="_blank"`` rather than the whole page.
"""

import base64
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.commercial.models import Certificate, Customer, Service, ServiceSubscription

User = get_user_model()

PDF_BYTES = b'%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF'
# Minimal valid 1x1 PNG (Pillow can open/resize it for ImageField paths).
PNG_BYTES = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
)


def assert_file_anchor_not_blank_tab(test_case, content, file_url):
    """Assert the uploaded file's anchor is not ``<a href="<url>" target="_blank">``."""
    needle = ('href="' + file_url + '" target="_blank"').encode()
    test_case.assertNotIn(needle, content)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class CommercialFilePreviewModalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@example.com', 'pass')
        self.user.first_name = 'Admin'
        self.user.last_name = 'Test'
        self.user.email = 'admin@example.com'
        self.user.save()

        # Public service carrying BOTH a pdf and an image. The template only
        # shows the pdf button inside `field_pdf` (public) and the image link
        # inside `field_image` (commercial, CSS-hidden), but both are rendered
        # into the HTML, so a single public object yields both markers.
        self.service = Service.objects.create(
            user=self.user,
            title='Servicio Publico',
            summary='Resumen de prueba',
            service_type='public',
            pdf=SimpleUploadedFile('doc.pdf', PDF_BYTES, 'application/pdf'),
            image=SimpleUploadedFile('img.png', PNG_BYTES, 'image/png'),
        )

        # Customer + subscription for the approve (upload certificate) view.
        self.customer_user = User.objects.create_user('cust', 'cust@example.com', 'pass')
        self.customer = Customer.objects.create(
            user=self.customer_user,
            client_type='juridica',
            account='1234567890123456',
            nit='12345678901',
            reeup='123.4.56789',
            address='Calle 1',
            phone='12345678',
            accept_terms=True,
        )
        self.sub_service = Service.objects.create(
            user=self.user, title='Sub Servicio', summary='s', service_type='public'
        )
        self.subscription = ServiceSubscription.objects.create(
            customer=self.customer, service=self.sub_service, payment_status='pending'
        )

    def test_servicio_update_no_blank_tab_pdf_and_fslightbox(self):
        self.client.force_login(self.user)
        url = reverse('commercial:servicio_update', kwargs={'uuid': self.service.uuid})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        # PDF preview uses the shared modal.
        self.assertIn(b'documentPdfModal', resp.content)
        self.assertIn(b'data-pdf-url=', resp.content)
        # Image preview uses fslightbox.
        self.assertIn(b'data-fslightbox', resp.content)
        # The uploaded pdf/image anchors must NOT open a blank tab.
        assert_file_anchor_not_blank_tab(self, resp.content, self.service.pdf.url)
        assert_file_anchor_not_blank_tab(self, resp.content, self.service.get_image_url())

    def test_servicio_update_fslightbox_script_loaded(self):
        # Requirement: any commercial servicio_update page loads fslightbox.
        self.client.force_login(self.user)
        url = reverse('commercial:servicio_update', kwargs={'uuid': self.service.uuid})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'fslightbox', resp.content)

    def test_suscripcion_approve_shows_current_certificate_in_modal(self):
        from django.utils import timezone

        # The approve view previews the most recent certificate (reverse
        # relation `object.certificates`), not a non-existent field on the
        # subscription itself.
        Certificate.objects.create(
            subscription=self.subscription,
            pdf=SimpleUploadedFile('cert.pdf', PDF_BYTES, 'application/pdf'),
            issued_date=timezone.now(),
        )
        self.client.force_login(self.user)
        url = reverse('commercial:suscripcion_approve', kwargs={'uuid': self.subscription.uuid})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'documentPdfModal', resp.content)
        self.assertIn(b'fslightbox', resp.content)
        # The current certificate's PDF previews in the shared modal.
        self.assertIn(b'data-pdf-url=', resp.content)
        cert = self.subscription.certificates.first()
        assert_file_anchor_not_blank_tab(self, resp.content, cert.pdf.url)
