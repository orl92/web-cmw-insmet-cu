"""Accessibility contract tests for the shared PDF viewer partials and JS.

Covers change 015-home-templates-ui Phase 1:
- pdf_preview.html renders the auto-initializable preview container
- pdf_modal.html toolbar controls expose accessible names
- The rendered canvas carries role="img" + aria-label (set in pdf-viewer.js)
- No dead `loadPdf(` invocations exist in templates or JS
- Real methods `loadPDF`/`loadNewPDF` remain in pdf-viewer.js
"""

import re
from pathlib import Path

from django.template.loader import render_to_string
from django.test import TestCase

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
