"""Accessibility contract tests for the uniform native PDF modal pattern.

Covers change 016-public-ui-ux (legacy PDF.js system removed):

- The single shared partial `templates/includes/home/document_card.html` renders
  an `<article class="card">` whose "Ver PDF" control is a `<button>` (not
  `href="#"`), carrying `data-bs-toggle="modal" data-bs-target="#documentPdfModal"
  data-pdf-url data-pdf-title`.
- `templates/includes/home/document_pdf_modal.html` provides exactly one modal
  (`id="documentPdfModal"`) with a lazy native `<object type="application/pdf">`
  (`id="documentPdfObject"`) and a `<a id="documentPdfDownload" download>` fallback.
- `static/dist/js/document-modal.js` lazy-sets the object `data` (and the
  download `href`) on `show.bs.modal` from the trigger's attributes, and clears
  them on hide — no double fetch, no PDF.js.
- Every PDF-bearing public template (avisos, tiempo, commentaries, note,
  publications, services public/commercial) delegates to these shared partials
  and loads only `document-modal.js`; there are NO remaining references to the
  old PDF.js assets (`pdf-viewer.js`, `pdf.min.js`, `pdf.worker.min.js`,
  `pdf-viewer.css`, `pdf_preview.html`, `pdf_modal.html`, `pdfPreviewContainer`,
  `modalDownloadLink`, `new PDFViewer(`).
"""

import re
from datetime import date, timedelta
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.meteo.models import Warning as MeteoWarning
from apps.meteo.models import WeatherReport
from apps.publications.models import Author, ScientificPublication

REPO_ROOT = Path(__file__).resolve().parents[3]

# Legacy PDF.js markers that must no longer appear in shipped code.
LEGACY_MARKERS = (
    'pdf-viewer.js',
    'pdf.min.js',
    'pdf.worker.min.js',
    'pdf-viewer.css',
    'pdf_preview.html',
    'pdf_modal.html',
    'pdfPreviewContainer',
    'modalDownloadLink',
    'new PDFViewer(',
)


class NoDeadLoadPdfCallsTests(TestCase):
    """Spec: no shipped *.html/*.js references the removed PDF.js assets."""

    SHIPPED_CODE_ROOTS = (
        REPO_ROOT / 'templates',
        REPO_ROOT / 'apps',
        REPO_ROOT / 'static',
    )

    def _shipped_html_and_js_files(self):
        for root in self.SHIPPED_CODE_ROOTS:
            yield from (path for pattern in ('*.html', '*.js') for path in root.rglob(pattern))

    def test_shipped_code_contains_no_legacy_pdf_js_markers(self):
        offenders = []
        for path in self._shipped_html_and_js_files():
            text = path.read_text(encoding='utf-8')
            # Skip the legacy files themselves (deleted by the cleanup pass).
            rel = str(path.relative_to(REPO_ROOT))
            if rel in (
                'static/dist/js/pdf-viewer.js',
                'static/dist/css/pdf-viewer.css',
                'static/dist/libs/PDF/pdf.min.js',
                'static/dist/libs/PDF/pdf.worker.min.js',
                'templates/includes/home/pdf_preview.html',
                'templates/includes/home/pdf_modal.html',
            ):
                continue
            # `document_pdf_modal.html` legitimately contains the substring
            # "pdf_modal.html"; strip it so the legacy marker check is exact.
            cleaned = text.replace('document_pdf_modal.html', '')
            for marker in LEGACY_MARKERS:
                if marker in cleaned:
                    offenders.append(f'{rel}: {marker}')
        self.assertEqual([], offenders)

    def test_shipped_code_contains_no_loadpdf_invocations(self):
        offenders = [
            str(path.relative_to(REPO_ROOT))
            for path in self._shipped_html_and_js_files()
            if 'loadPdf(' in path.read_text(encoding='utf-8')
        ]
        self.assertEqual([], offenders)


class AvisosLayoutSharedPartialTests(TestCase):
    """Tasks 2.1-2.4 — layouts/avisos.html delegates to the shared partials."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            'author', 'author@test.com', 'pass', first_name='A', last_name='U'
        )

    def _create_warning(self):
        return MeteoWarning.objects.create(
            warning_type='early',
            user=self.user,
            summary='Resumen del aviso de prueba',
            file='warning_pdfs/aviso.pdf',
            valid_until=timezone.now() + timedelta(days=1),
        )

    def _get_page(self):
        return self.client.get(reverse('home:warnings_early'))

    def test_preview_renders_through_partial_with_pdf_url(self):
        warning = self._create_warning()
        response = self._get_page()
        pdf_url = reverse('home:warning_pdf', args=[warning.uuid]) + '?inline=1'
        self.assertContains(response, f'data-pdf-url="{pdf_url}"')
        self.assertContains(response, 'id="documentPdfModal"')

    def test_each_warning_gets_its_own_preview_container(self):
        w1 = self._create_warning()
        w2 = self._create_warning()
        html = self._get_page().content.decode()
        pdf_url_1 = reverse('home:warning_pdf', args=[w1.uuid]) + '?inline=1'
        pdf_url_2 = reverse('home:warning_pdf', args=[w2.uuid]) + '?inline=1'
        # One "Ver PDF" trigger per warning, each linking its own public URL.
        self.assertEqual(1, html.count(f'data-pdf-url="{pdf_url_1}"'))
        self.assertEqual(1, html.count(f'data-pdf-url="{pdf_url_2}"'))
        self.assertEqual(2, html.count('data-pdf-url='))
        self.assertEqual(1, html.count('id="documentPdfModal"'))

    def test_modal_comes_from_shared_partial_exactly_once(self):
        self._create_warning()
        html = self._get_page().content.decode()
        self.assertEqual(1, html.count('id="documentPdfModal"'))
        self.assertIn('id="documentPdfDownload"', html)

    def test_card_body_drops_markdown_class(self):
        self._create_warning()
        self.assertNotContains(self._get_page(), 'card-body markdown')

    def test_no_duplicate_h1_in_content(self):
        self._create_warning()
        self.assertNotContains(self._get_page(), '<h1')

    def test_no_per_template_viewer_init_script(self):
        self._create_warning()
        html = self._get_page().content.decode()
        self.assertNotIn('new PDFViewer({', html)
        self.assertNotIn('Inicializando visores de PDF para avisos', html)
        self.assertIn('dist/js/document-modal.js', html)
        self.assertNotIn('dist/js/pdf-viewer.js', html)
        self.assertNotIn('pdf.worker.min.js', html)


class PublicationsSharedPartialTests(TestCase):
    """Publications list delegates to the shared document card + modal."""

    @classmethod
    def setUpTestData(cls):
        cls.author = Author.objects.create(first_name='Ada', last_name='Lovelace')

    def _create_publication(self, title='Paper A', with_pdf=True):
        pdf = None
        if with_pdf:
            pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        return ScientificPublication.objects.create(
            title=title,
            author=self.author,
            summary='Resumen de la publicación',
            publication_date=date.today(),
            pdf=pdf,
        )

    def _get_page(self):
        return self.client.get(reverse('home:publications'))

    def test_shared_modal_and_loader_present(self):
        self._create_publication()
        response = self._get_page()
        self.assertContains(response, 'id="documentPdfModal"')
        self.assertContains(response, 'id="documentPdfDownload"')
        self.assertContains(response, 'dist/js/document-modal.js')
        # Legacy PDF.js assets must be gone.
        self.assertNotContains(response, 'dist/js/pdf-viewer.js')
        self.assertNotContains(response, 'pdf.worker.min.js')
        html = response.content.decode()
        self.assertNotIn('pdfPreviewContainer', html)

    def test_ver_pdf_button_carries_url_and_title(self):
        pub = self._create_publication(title='Deep Learning Paper')
        html = self._get_page().content.decode()
        # The trigger is now a <button> (no href="#") carrying both attributes.
        pdf_url = reverse('home:publication_pdf', args=[pub.uuid]) + '?inline=1'
        pattern = (
            rf'data-pdf-url="{re.escape(pdf_url)}"'
            rf'[^>]*data-pdf-title="{re.escape(pub.title)}"'
        )
        self.assertRegex(html, pattern)

    def test_only_publications_with_pdf_render_a_trigger(self):
        self._create_publication(title='Con PDF')
        self._create_publication(title='Sin PDF', with_pdf=False)
        html = self._get_page().content.decode()
        # Exactly one shared modal, regardless of publication count.
        self.assertEqual(1, html.count('id="documentPdfModal"'))
        self.assertNotIn('pdfPreviewContainer', html)


class ReportsSharedPartialTests(TestCase):
    """Report pages (today/tomorrow/commentary/note) delegate to the shared partials."""

    REPORT_PAGES = (
        ('today', 'home:weather_today'),
        ('tomorrow', 'home:weather_tomorrow'),
        ('commentary', 'home:weather_commentary'),
        ('note', 'home:weather_note'),
    )

    PAGE_TITLES = {
        'today': 'El Tiempo para Hoy',
        'tomorrow': 'El Tiempo para Mañana',
        'commentary': 'Comentario del Tiempo',
        'note': 'Nota Meteorológica',
    }

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            'author', 'author@test.com', 'pass', first_name='A', last_name='U'
        )

    def _create_report(self, report_type, **overrides):
        fields = dict(
            user=self.user,
            summary='Resumen consistente del reporte',
            file='report_pdfs/informe.pdf',
            report_type=report_type,
        )
        fields.update(overrides)
        return WeatherReport.objects.create(**fields)

    def _get_page(self, url_name):
        return self.client.get(reverse(url_name))

    def test_preview_renders_through_shared_partial_with_data_pdf_url(self):
        for report_type, url_name in self.REPORT_PAGES:
            with self.subTest(report=report_type):
                report = self._create_report(report_type)
                html = self._get_page(url_name).content.decode()
                pdf_url = reverse('home:weather_report_pdf', args=[report.uuid])
                self.assertIn(
                    f'data-pdf-url="{pdf_url}?inline=1"',
                    html,
                )
                # Native <object> modal pattern for every report type.
                self.assertIn('id="documentPdfModal"', html)
                self.assertIn('id="documentPdfDownload"', html)

    def test_card_body_drops_markdown_class(self):
        for report_type, url_name in self.REPORT_PAGES:
            with self.subTest(report=report_type):
                self._create_report(report_type)
                self.assertNotContains(self._get_page(url_name), 'card-body markdown')

    def test_no_duplicate_h1_title_comes_from_page_header(self):
        for report_type, url_name in self.REPORT_PAGES:
            with self.subTest(report=report_type):
                self._create_report(report_type)
                response = self._get_page(url_name)
                self.assertNotContains(response, '<h1')
                html = response.content.decode()
                title = re.escape(self.PAGE_TITLES[report_type])
                pattern = rf'<h2 class="page-title">\s*{title}\s*</h2>'
                self.assertRegex(html, pattern)

    def test_no_per_template_viewer_init_script(self):
        for report_type, url_name in self.REPORT_PAGES:
            with self.subTest(report=report_type):
                self._create_report(report_type)
                html = self._get_page(url_name).content.decode()
                self.assertNotIn('new PDFViewer({', html)
                # Native <object> modal loader everywhere.
                self.assertIn('dist/js/document-modal.js', html)
                self.assertNotIn('dist/js/pdf-viewer.js', html)
                self.assertNotIn('pdf.worker.min.js', html)

    def test_modal_comes_from_shared_partial_exactly_once(self):
        for report_type, url_name in self.REPORT_PAGES:
            with self.subTest(report=report_type):
                self._create_report(report_type)
                html = self._get_page(url_name).content.decode()
                self.assertEqual(1, html.count('id="documentPdfModal"'))
                self.assertIn('id="documentPdfDownload"', html)

    def test_ver_pdf_trigger_carries_url_and_title(self):
        for report_type, url_name in self.REPORT_PAGES:
            with self.subTest(report=report_type):
                report = self._create_report(report_type)
                html = self._get_page(url_name).content.decode()
                pdf_url = reverse('home:weather_report_pdf', args=[report.uuid]) + '?inline=1'
                pattern = (
                    rf'data-pdf-url="{re.escape(pdf_url)}"'
                    rf'[^>]*data-pdf-title="[^"]+"'
                )
                self.assertRegex(html, pattern)

    def test_summary_rendered_not_content_for_all_reports(self):
        for report_type, url_name in self.REPORT_PAGES:
            with self.subTest(report=report_type):
                self._create_report(
                    report_type,
                    summary='Resumen consistente del reporte',
                    content='Contenido alterno que no debe mostrarse',
                )
                response = self._get_page(url_name)
                self.assertContains(response, 'Resumen consistente del reporte')
                self.assertNotContains(response, 'Contenido alterno que no debe mostrarse')

    def test_all_four_templates_render_summary_with_sanitize_filter(self):
        for report_type, url_name in self.REPORT_PAGES:
            with self.subTest(report=report_type):
                self._create_report(
                    report_type,
                    summary='Resumen seguro<script>alert(1)</script>',
                )
                response = self._get_page(url_name)
                self.assertContains(response, 'Resumen seguro')
                # The literal malicious payload must be neutralized (escaped),
                # not executed. Legit <script src=...> library tags are fine.
                self.assertNotContains(response, '<script>alert(1)</script>')


class PublicPdfServeTests(TestCase):
    """PublicServeFileView: the home portal serves PDFs inline without login,
    with X-Frame-Options: SAMEORIGIN (so the <object> embeds them in Firefox)."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            'author', 'author@test.com', 'pass', first_name='A', last_name='U'
        )
        file = SimpleUploadedFile('informe.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        cls.report = WeatherReport.objects.create(
            user=cls.user,
            summary='Resumen del reporte',
            file=file,
            report_type='today',
        )

    def test_inline_serves_with_sameorigin_and_pdf_type(self):
        self.client.logout()
        url = reverse('home:weather_report_pdf', args=[self.report.uuid]) + '?inline=1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('inline', response['Content-Disposition'])
        self.assertEqual(response['X-Frame-Options'], 'SAMEORIGIN')

    def test_inline_serves_without_login(self):
        url = reverse('home:weather_report_pdf', args=[self.report.uuid]) + '?inline=1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_attachment_keeps_xframe_deny(self):
        url = reverse('home:weather_report_pdf', args=[self.report.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertEqual(response['X-Frame-Options'], 'DENY')

    def test_unknown_uuid_returns_404(self):
        url = reverse('home:weather_report_pdf', args=['00000000-0000-0000-0000-000000000000'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
