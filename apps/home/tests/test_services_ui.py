"""UI contract tests for the services pages (015-home-templates-ui, Phase 5).

Covers tasks 5.1-5.4:
- services/public.html and services/commercial.html render Django's page_obj
  through the Tabler pagination component (ul.pagination > li.page-item >
  a.page-link), replacing the manual `.pagination`/`.step-links` markup.
- Service titles and summaries render as plain <h3>/<p> text, not as href-less
  <a> wrappers.
- The "Ver PDF" trigger keeps data-pdf-url + data-pdf-title so
  PDFViewerManager's show.bs.modal handler can load the modal (the per-template
  window.viewer/loadPdf script was deleted).
"""

import re
from datetime import timedelta
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.commercial.models import Certificate, Customer, Service, ServiceSubscription
from apps.core.models import SiteConfiguration

REPO_ROOT = Path(__file__).resolve().parents[3]


def _disable_maintenance_mode():
    SiteConfiguration.objects.update_or_create(defaults={'maintenance_mode': False})


class ServicesPublicUiTests(TestCase):
    """Tasks 5.1-5.3 — pages/home/services/public.html."""

    PAGINATE_BY = 10

    @classmethod
    def setUpTestData(cls):
        cls.provider = User.objects.create_user('provider', 'provider@test.com', 'pass')

    def _create_services(self, count):
        for index in range(count):
            Service.objects.create(
                user=self.provider,
                title=f'Servicio público {index}',
                summary=f'Resumen del servicio {index}',
                service_type=Service.PUBLIC,
                pdf=f'service_pdfs/public-{index}.pdf',
            )

    def _get_page(self, **query):
        return self.client.get(reverse('home:services_public'), query)

    def test_renders_tabler_pagination_bound_to_page_obj(self):
        # 21 public services with paginate_by=10 -> three pages. Request the
        # middle page so both the previous ("Página anterior") and next
        # ("Página siguiente") pagination links render with real aria-labels.
        self._create_services(self.PAGINATE_BY * 2 + 1)
        html = self._get_page(page=2).content.decode()
        self.assertIn('<ul class="pagination"', html)
        self.assertRegex(html, r'<li class="page-item[^"]*">\s*<a class="page-link"')
        self.assertIn('aria-label="Página anterior"', html)
        self.assertIn('aria-label="Página siguiente"', html)

    def test_pagination_links_use_page_param_and_mark_active_item(self):
        self._create_services(self.PAGINATE_BY + 1)
        html = self._get_page(page=2).content.decode()
        # Previous/first links point back to page 1; current item is marked.
        self.assertIn('href="?page=1"', html)
        self.assertIn('page-item active', html)
        self.assertIn('aria-current="page"', html)
        # The old manual step-links markup must be gone entirely.
        self.assertNotIn('step-links', html)
        self.assertNotIn('&laquo; primera', html)

    def test_single_page_renders_no_pagination_nav(self):
        self._create_services(2)
        html = self._get_page().content.decode()
        self.assertNotIn('<ul class="pagination"', html)

    def test_titles_render_as_headings_not_links(self):
        self._create_services(2)
        html = self._get_page().content.decode()
        self.assertIn('<h3 class="mb-0 card-title">Servicio público 0</h3>', html)
        self.assertIn('<p class="text-secondary mt-2">Resumen del servicio 0</p>', html)
        self.assertNotContains(self._get_page(), '<h3 class="mb-0 card-title"><a>')
        self.assertNotContains(self._get_page(), '<p class="text-secondary mt-2"><a>')

    def test_ver_pdf_trigger_keeps_data_pdf_url_and_title(self):
        self._create_services(1)
        service = Service.objects.get(title='Servicio público 0')
        html = self._get_page().content.decode()
        pdf_url = reverse('home:service_pdf', args=[service.uuid]) + '?inline=1'
        pattern = (
            rf'data-pdf-url="{re.escape(pdf_url)}"'
            rf'[^>]*data-pdf-title="Servicio público 0"'
        )
        self.assertRegex(html, pattern)


class ServicesCommercialUiTests(TestCase):
    """Task 5.4 — pages/home/services/commercial.html."""

    PAGINATE_BY = 10

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            'client', 'client@test.com', 'pass', first_name='Cliente', last_name='Prueba'
        )
        cls.provider = User.objects.create_user(
            'vendor', 'vendor@test.com', 'pass', first_name='Vendedor', last_name='Prueba'
        )

    def _login_with_subscriptions(self, count=1):
        customer = Customer.objects.create(
            user=self.user,
            client_type=Customer.ClientType.NATURAL,
            account='1234567890123456',
            agency_bank='BANDEC',
            address='Calle 10 e/ 11 y 13',
            phone='+5350000000',
        )
        subscriptions = []
        for index in range(count):
            service = Service.objects.create(
                user=self.provider,
                title=f'Servicio comercial {index}',
                summary=f'Resumen comercial {index}',
                service_type=Service.COMMERCIAL,
            )
            subscription = ServiceSubscription.objects.create(
                customer=customer,
                service=service,
                start_date=timezone.now() - timedelta(days=10 - index),
                end_date=timezone.now() + timedelta(days=30),
                payment_status='paid',
                payment_method='transfer',
            )
            Certificate.objects.create(
                subscription=subscription,
                pdf=f'certificate_pdfs/cert-{index}.pdf',
            )
            subscriptions.append(subscription)
        self.client.force_login(self.user)
        return subscriptions

    def _get_page(self, **query):
        return self.client.get(reverse('home:services_commercial'), query)

    def test_renders_tabler_pagination_bound_to_page_obj(self):
        # 3 pages of subscriptions; request the middle page so both previous
        # and next pagination links render with real aria-labels.
        self._login_with_subscriptions(self.PAGINATE_BY * 2 + 1)
        html = self._get_page(page=2).content.decode()
        self.assertIn('<ul class="pagination"', html)
        self.assertRegex(html, r'<li class="page-item[^"]*">\s*<a class="page-link"')
        self.assertIn('aria-label="Página anterior"', html)
        self.assertIn('aria-label="Página siguiente"', html)

    def test_titles_render_as_headings_not_links(self):
        self._login_with_subscriptions(2)
        html = self._get_page().content.decode()
        self.assertIn('<h3 class="mb-0">Servicio comercial 0</h3>', html)
        self.assertIn('<p class="mb-0 text-secondary">Resumen comercial 0</p>', html)
        self.assertNotContains(self._get_page(), '<h3 class="mb-0"><a>')
        self.assertNotContains(self._get_page(), '<p class="mb-0 text-secondary"><a>')

    def test_ver_pdf_trigger_keeps_data_pdf_url_and_title(self):
        subscriptions = self._login_with_subscriptions(1)
        certificate = subscriptions[0].certificates.first()
        cert_url = reverse('commercial:certificado_pdf', args=[certificate.uuid]) + '?inline=1'
        html = self._get_page().content.decode()
        pattern = (
            rf'data-pdf-url="{re.escape(cert_url)}"'
            rf'[^>]*data-pdf-title="Servicio comercial 0"'
        )
        self.assertRegex(html, pattern)


class ServicesCommercialStaffButtonTests(TestCase):
    """Task 6.3 — staff/management buttons on the public commercial view."""

    @classmethod
    def setUpTestData(cls):
        _disable_maintenance_mode()
        cls.provider = User.objects.create_user(
            'provider2', 'provider2@test.com', 'pass', first_name='Vendedor', last_name='Dos'
        )
        cls.staff = User.objects.create_user(
            'staffcom',
            'staffcom@test.com',
            'pass',
            is_staff=True,
            first_name='Staff',
            last_name='Com',
        )
        cls.anon_service = Service.objects.create(
            user=cls.provider,
            title='Comercial anónimo',
            summary='Sum',
            service_type=Service.COMMERCIAL,
        )

    def _get_page(self):
        return self.client.get(reverse('home:services_commercial_public'))

    def test_staff_sees_edit_and_new_service_buttons(self):
        update_url = reverse('commercial:servicio_update', args=[self.anon_service.uuid])
        self.client.force_login(self.staff)
        html = self._get_page().content.decode()
        self.assertIn('Editar', html)
        self.assertIn(update_url, html)
        self.assertIn('Nuevo servicio', html)
        self.assertIn(reverse('commercial:servicio_create'), html)

    def test_anonymous_sees_no_management_buttons(self):
        self.client.logout()
        html = self._get_page().content.decode()
        self.assertNotIn('Editar', html)
        self.assertNotIn('Nuevo servicio', html)

    def test_pending_non_qr_shows_invoice_guidance(self):
        client_user = User.objects.create_user(
            'clientnonq',
            'clientnonq@test.com',
            'pass',
            first_name='C',
            last_name='P',
        )
        customer = Customer.objects.create(
            user=client_user,
            client_type=Customer.ClientType.NATURAL,
            account='1234567890123456',
            agency_bank='BANDEC',
            address='Addr',
            phone='12345678',
        )
        ServiceSubscription.objects.create(
            customer=customer,
            service=self.anon_service,
            payment_status='pending',
            payment_method='transfer',
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=10),
        )
        self.client.force_login(client_user)
        html = self._get_page().content.decode()
        self.assertIn('Ver factura', html)
        self.assertIn(reverse('commercial:factura_list'), html)
