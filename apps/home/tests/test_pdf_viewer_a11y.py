"""Accessibility contract tests for the shared PDF viewer partials and JS.

Covers change 015-home-templates-ui:
- Phase 1: pdf_preview.html renders the auto-initializable preview container,
  pdf_modal.html toolbar controls expose accessible names, the rendered canvas
  carries role="img" + aria-label (set in pdf-viewer.js), no dead `loadPdf(`
  invocations exist in partials or JS, real methods loadPDF/loadNewPDF remain.
- Phase 2: layouts/avisos.html delegates previews and modal to the shared
  partials with unique per-warning container ids, drops the `.markdown` card
  body and duplicate <h1>, and keeps no inline viewer init script.
- Phase 3: pages/home/institution/publications.html renders each publication
  preview through the shared partial (unique ids + data-pdf-url), drops its
  manual `new PDFViewer(...)` init loop, keeps exactly one shared modal with
  the download fallback, and its "Ver PDF" trigger carries data-pdf-url +
  data-pdf-title for manager delegation.
"""

import re
from datetime import date, timedelta
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.meteo.models import Warning as MeteoWarning
from apps.publications.models import Author, ScientificPublication

REPO_ROOT = Path(__file__).resolve().parents[3]
PDF_VIEWER_JS = REPO_ROOT / 'static' / 'dist' / 'js' / 'pdf-viewer.js'


class PdfPreviewPartialTests(TestCase):
    """Task 1.1 — templates/includes/home/pdf_preview.html."""

    def _render(self, **context):
        return render_to_string('includes/home/pdf_preview.html', context)

    def test_preview_renders_auto_init_container_with_pdf_url(self):
        html = self._render(pdf_url='/media/reports/aviso.pdf', pdf_title='Aviso 01')
        self.assertIn('id="pdfPreviewContainer"', html)
        self.assertIn('id="pdfPages"', html)
        self.assertIn('data-pdf-url="/media/reports/aviso.pdf"', html)

    def test_preview_renders_download_fallback_with_accessible_name(self):
        html = self._render(pdf_url='/media/reports/aviso.pdf', pdf_title='Aviso 01')
        self.assertIn('href="/media/reports/aviso.pdf"', html)
        self.assertIn('aria-label="Descargar PDF: Aviso 01"', html)
        self.assertIn('Descargar PDF', html)

    def test_preview_triangulates_with_distinct_context_values(self):
        html = self._render(
            pdf_url='/media/publications/paper.pdf',
            pdf_title='Paper científico',
        )
        self.assertIn('data-pdf-url="/media/publications/paper.pdf"', html)
        self.assertIn('aria-label="Descargar PDF: Paper científico"', html)


class PdfModalPartialTests(TestCase):
    """Task 1.2 — accessible names on the five toolbar controls + fallback link."""

    def setUp(self):
        self.html = render_to_string('includes/home/pdf_modal.html')

    def test_toolbar_controls_have_aria_labels(self):
        expected_labels = (
            ('modalPrevPage', 'Página anterior'),
            ('modalNextPage', 'Página siguiente'),
            ('modalZoomOut', 'Alejar'),
            ('modalZoomIn', 'Acercar'),
            ('modalFitWidth', 'Ajustar al ancho'),
        )
        for control_id, label in expected_labels:
            with self.subTest(control=control_id):
                # The button carrying this id must also carry its accessible name.
                pattern = rf'id="{control_id}"[^>]*aria-label="{re.escape(label)}"'
                self.assertRegex(self.html, pattern)

    def test_has_download_fallback_link(self):
        self.assertIn('id="modalDownloadLink"', self.html)
        self.assertIn('aria-label="Descargar PDF"', self.html)

    def test_page_info_is_announced_politely(self):
        # Task 1.3 (markup half): page info is an aria-live region so screen
        # readers announce page changes without interrupting.
        pattern = r'id="modalPageInfo"[^>]*aria-live="polite"'
        self.assertRegex(self.html, pattern)


class PdfViewerJsAccessibilityTests(TestCase):
    """Tasks 1.3 and 1.4 — canvas text alternative, download wiring, real API.

    There is no JS test runner in this project (django_unittest only), so the
    JS contract is asserted against the shipped source file, mirroring the
    spec's grep-based scenarios.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.js = PDF_VIEWER_JS.read_text(encoding='utf-8')

    def test_render_page_canvas_is_labeled_as_image(self):
        self.assertIn("canvas.setAttribute('role', 'img')", self.js)

    def test_render_page_canvas_label_names_the_current_page(self):
        match = re.search(
            r"canvas\.setAttribute\(\s*'aria-label',\s*`Página \$\{([^}]+)\} del documento`\s*\)",
            self.js,
        )
        self.assertIsNotNone(match, 'renderPage must set a per-page aria-label')
        self.assertIn('pageNumber', match.group(1))

    def test_load_new_pdf_wires_modal_download_link(self):
        # The modal download fallback must receive the active PDF URL.
        self.assertIn('modalDownloadLink', self.js)
        self.assertRegex(self.js, r'\.href\s*=\s*url\b')

    def test_real_methods_are_preserved(self):
        self.assertIn('async loadPDF(', self.js)
        self.assertIn('async loadNewPDF(', self.js)


class NoDeadLoadPdfCallsTests(TestCase):
    """Spec: no file shipped by this change may call `loadPdf(`.

    Scoped to the Phase 1 deliverables (shared partials + viewer script).
    The full-repo sweep belongs to final verification (task 9.2), once
    later phases delete the legacy callers in services templates.
    """

    PHASE1_FILES = (
        REPO_ROOT / 'templates' / 'includes' / 'home' / 'pdf_preview.html',
        REPO_ROOT / 'templates' / 'includes' / 'home' / 'pdf_modal.html',
        REPO_ROOT / 'static' / 'dist' / 'js' / 'pdf-viewer.js',
    )

    def test_phase1_deliverables_contain_no_loadpdf_invocations(self):
        offenders = [
            str(path.relative_to(REPO_ROOT))
            for path in self.PHASE1_FILES
            if 'loadPdf(' in path.read_text(encoding='utf-8')
        ]
        self.assertEqual([], offenders)

    def test_dead_callers_are_documented_outside_phase1_scope(self):
        # Sanity for the scoping decision itself: legacy callers live only in
        # the services templates slated for removal in a later phase.
        legacy = [
            path
            for name in ('services/public.html', 'services/commercial.html')
            if 'loadPdf('
            in (REPO_ROOT / 'apps' / 'home' / 'templates' / 'pages' / 'home' / name).read_text(
                encoding='utf-8'
            )
            for path in [REPO_ROOT / 'apps' / 'home' / 'templates' / 'pages' / 'home' / name]
        ]
        self.assertEqual(2, len(legacy))


class PdfPreviewPartialContainerIdTests(TestCase):
    """Task 2.2 — pdf_preview.html must support unique per-object container ids.

    The avisos layout loops over warnings, so every preview needs a distinct
    id (`pdfPreviewContainer-N`) for PDFViewerManager.initializeAll() to pick
    it up via `[id^="pdfPreviewContainer-"]` (pdf-viewer.js:440). Without a
    suffix the partial keeps the exact Phase 1 ids.
    """

    def _render(self, **context):
        return render_to_string('includes/home/pdf_preview.html', context)

    def test_default_ids_preserved_without_suffix(self):
        html = self._render(pdf_url='/media/reports/aviso.pdf')
        self.assertIn('id="pdfPreviewContainer"', html)
        self.assertIn('id="pdfPages"', html)
        self.assertIn('data-pdf-url="/media/reports/aviso.pdf"', html)

    def test_suffix_yields_unique_container_and_pages_ids(self):
        html = self._render(pdf_url='/media/warnings/a.pdf', preview_suffix=3)
        self.assertIn('id="pdfPreviewContainer-3"', html)
        self.assertIn('id="pdfPages-3"', html)
        self.assertIn('data-pdf-url="/media/warnings/a.pdf"', html)

    def test_download_fallback_survives_suffixed_render(self):
        html = self._render(
            pdf_url='/media/warnings/b.pdf',
            pdf_title='Aviso 02',
            preview_suffix=2,
        )
        self.assertIn('href="/media/warnings/b.pdf"', html)
        self.assertIn('aria-label="Descargar PDF: Aviso 02"', html)


class AvisosLayoutSharedPartialTests(TestCase):
    """Tasks 2.1-2.4 — layouts/avisos.html delegates to the shared partials.

    Spec scenario "Avisos render is deduplicated and semantic": the rendered
    page carries the shared preview containers and modal include, drops the
    `.markdown` card body and the duplicate <h1>, and keeps no inline viewer
    init script (the manager auto-runs on DOMContentLoaded).
    """

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
        self._create_warning()
        response = self._get_page()
        self.assertContains(response, 'id="pdfPreviewContainer-1"')
        self.assertContains(response, 'id="pdfPages-1"')
        self.assertContains(
            response,
            'data-pdf-url="http://testserver/media/warning_pdfs/aviso.pdf"',
        )

    def test_each_warning_gets_its_own_preview_container(self):
        self._create_warning()
        self._create_warning()
        response = self._get_page()
        self.assertContains(response, 'id="pdfPreviewContainer-1"')
        self.assertContains(response, 'id="pdfPreviewContainer-2"')

    def test_modal_comes_from_shared_partial_exactly_once(self):
        self._create_warning()
        html = self._get_page().content.decode()
        # Exactly one modal: the shared partial, not a duplicated inline copy.
        self.assertEqual(1, html.count('id="pdfModal"'))
        # Partial-only marker: the download fallback link added in Phase 1.
        self.assertIn('id="modalDownloadLink"', html)

    def test_card_body_drops_markdown_class(self):
        self._create_warning()
        self.assertNotContains(self._get_page(), 'card-body markdown')

    def test_no_duplicate_h1_in_content(self):
        self._create_warning()
        # The title lives in page_header (layouts/home.html); no second <h1>.
        self.assertNotContains(self._get_page(), '<h1')

    def test_no_per_template_viewer_init_script(self):
        self._create_warning()
        html = self._get_page().content.decode()
        self.assertNotIn('new PDFViewer({', html)
        # Task 2.4: the redundant DOMContentLoaded no-op listener is gone;
        # library loads + workerSrc config must remain for the viewer to work.
        self.assertNotIn('Inicializando visores de PDF para avisos', html)
        self.assertIn('dist/js/pdf-viewer.js', html)


class PublicationsSharedPartialTests(TestCase):
    """Tasks 3.1-3.2 — publications.html delegates to the shared partials.

    Spec scenario "Publications preview auto-initializes": each preview
    container carries data-pdf-url (unique ids via preview_suffix) and no
    `new PDFViewer({` init loop remains; the manager opens the modal from
    the trigger's data-pdf-url / data-pdf-title via show.bs.modal.
    """

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

    def test_preview_renders_through_partial_with_data_pdf_url(self):
        pub = self._create_publication()
        response = self._get_page()
        self.assertContains(response, 'id="pdfPreviewContainer-1"')
        self.assertContains(response, 'id="pdfPages-1"')
        self.assertContains(response, f'data-pdf-url="{pub.pdf.url}"')

    def test_each_publication_gets_its_own_preview_container(self):
        self._create_publication(title='Paper A')
        self._create_publication(title='Paper B')
        response = self._get_page()
        self.assertContains(response, 'id="pdfPreviewContainer-1"')
        self.assertContains(response, 'id="pdfPreviewContainer-2"')

    def test_only_publications_with_pdf_render_a_preview_container(self):
        pub = self._create_publication(title='Con PDF')
        self._create_publication(title='Sin PDF', with_pdf=False)
        html = self._get_page().content.decode()
        self.assertEqual(1, html.count('pdfPreviewContainer'))
        self.assertIn(f'data-pdf-url="{pub.pdf.url}"', html)

    def test_no_per_template_viewer_init_script(self):
        self._create_publication()
        html = self._get_page().content.decode()
        self.assertNotIn('new PDFViewer({', html)
        # Library loads + workerSrc config must remain for the viewer to work.
        self.assertIn('dist/js/pdf-viewer.js', html)
        self.assertIn('pdf.worker.min.js', html)

    def test_modal_comes_from_shared_partial_exactly_once(self):
        self._create_publication()
        html = self._get_page().content.decode()
        # Task 3.2: exactly one modal — the shared partial with its
        # Phase 1 download fallback link ("Descargar PDF").
        self.assertEqual(1, html.count('id="pdfModal"'))
        self.assertIn('id="modalDownloadLink"', html)
        self.assertIn('Descargar PDF', html)

    def test_ver_pdf_trigger_carries_url_and_title(self):
        pub = self._create_publication(title='Deep Learning Paper')
        html = self._get_page().content.decode()
        # The manager's show.bs.modal handler reads both attributes to
        # auto-load the modal (loadNewPDF), so the trigger needs both.
        pattern = (
            rf'data-pdf-url="{re.escape(pub.pdf.url)}"'
            rf'[^>]*data-pdf-title="Deep Learning Paper"'
        )
        self.assertRegex(html, pattern)
