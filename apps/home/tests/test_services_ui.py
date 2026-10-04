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
from decimal import Decimal
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.defaultfilters import date as django_date_filter
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.commercial.models import (
    Certificate,
    Customer,
    Invoice,
    InvoiceItem,
    Service,
    ServiceSubscription,
)
from apps.core.models import SiteConfiguration
from apps.home.views.servicios.comerciales.views import CommercialServicesListView

REPO_ROOT = Path(__file__).resolve().parents[3]


def _disable_maintenance_mode():
    SiteConfiguration.objects.update_or_create(defaults={'maintenance_mode': False})


class PaymentMethodIconFilterTests(TestCase):
    """payment-method-icon — unit test for the templatetag filter."""

    def test_qr_maps_to_qrcode(self):
        from apps.core.templatetags.utils_filters import payment_method_icon

        self.assertEqual(payment_method_icon('qr'), 'ti-qrcode')

    def test_transfer_maps_to_building_bank(self):
        from apps.core.templatetags.utils_filters import payment_method_icon

        self.assertEqual(payment_method_icon('transfer'), 'ti-building-bank')

    def test_presencial_maps_to_building_store(self):
        from apps.core.templatetags.utils_filters import payment_method_icon

        self.assertEqual(payment_method_icon('presencial'), 'ti-building-store')

    def test_unknown_defaults_to_credit_card(self):
        from apps.core.templatetags.utils_filters import payment_method_icon

        self.assertEqual(payment_method_icon('unknown'), 'ti-credit-card')

    def test_none_defaults_to_credit_card(self):
        from apps.core.templatetags.utils_filters import payment_method_icon

        self.assertEqual(payment_method_icon(None), 'ti-credit-card')


class ServicesPublicUiTests(TestCase):
    """pages/home/services/public.html."""

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
        self.assertIn('<ul class="pagination pagination-sm', html)
        self.assertRegex(html, r'<li class="page-item[^"]*">\s*<a [^>]*class="page-link"')
        self.assertIn('aria-label="Página anterior"', html)
        self.assertIn('aria-label="Página siguiente"', html)

    def test_pagination_links_use_page_param_and_report_position(self):
        self._create_services(self.PAGINATE_BY + 1)
        html = self._get_page(page=2).content.decode()
        # Previous/first links point back to page 1, and the compact
        # component reports the current position ("Pág. 2 de 2").
        self.assertIn('href="?page=1"', html)
        self.assertIn('<span class="page-link">Pág. 2 de 2</span>', html)
        # The pagination must not ship the manual step-links markup.
        self.assertNotIn('step-links', html)
        self.assertNotIn('&laquo; primera', html)
        self.assertNotIn('aria-current="page"', html)

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

    def test_metadata_autor_and_publicado_on_separate_lines(self):
        # Mismo estilo que servicios comerciales y Mis Servicios: autor y
        # fecha en líneas separadas (mb-2) con título sugerente "Publicado:".
        User.objects.filter(pk=self.provider.pk).update(first_name='Yoilán', last_name='Meteoro')
        self.provider.refresh_from_db()
        self._create_services(1)
        html = self._get_page().content.decode()
        self.assertIn('Autor: <strong>Yoilán Meteoro</strong>', html)
        self.assertRegex(html, r'Publicado: <strong>\d{1,2}/\d{1,2}/\d{4}</strong>')
        # Las líneas van dentro de un contenedor columna con separación mb-2.
        self.assertIn('d-flex flex-column flex-grow-1 text-secondary mb-3', html)
        self.assertNotIn('d-flex flex-wrap gap-2 text-secondary mt-auto', html)


class ServicesCommercialUiTests(TestCase):
    """pages/home/services/commercial.html."""

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
        self.assertIn('<ul class="pagination pagination-sm', html)
        self.assertRegex(html, r'<li class="page-item[^"]*">\s*<a [^>]*class="page-link"')
        self.assertIn('aria-label="Página anterior"', html)
        self.assertIn('aria-label="Página siguiente"', html)

    def test_titles_link_to_detail_and_summary_is_plain_text(self):
        subscriptions = self._login_with_subscriptions(2)
        html = self._get_page().content.decode()
        detail_url = reverse(
            'home:services_commercial_detail', args=[subscriptions[0].service.uuid]
        )
        self.assertIn(f'href="{detail_url}"', html)
        self.assertIn('class="text-decoration-none text-reset">Servicio comercial 0</a>', html)
        self.assertIn('<p class="text-secondary">Resumen comercial 0</p>', html)
        # No href-less link wrappers around the summary.
        self.assertNotContains(self._get_page(), '<p class="text-secondary"><a')

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


class CommercialServicesListViewStateScopeTests(TestCase):
    """mis-servicios-cliente — CommercialServicesListView muestra TODAS las
    suscripciones del cliente (requested, pending, paid, expired), ya no solo
    las pagadas activas; el Case/When ordena requested -> pending -> paid ->
    expired."""

    @classmethod
    def setUpTestData(cls):
        _disable_maintenance_mode()
        cls.provider = User.objects.create_user(
            'allstatesprov', 'allstatesprov@test.com', 'pass', first_name='P', last_name='V'
        )
        cls.client_user = User.objects.create_user(
            'allstatescli', 'allstatescli@test.com', 'pass', first_name='C', last_name='V'
        )
        cls.customer = Customer.objects.create(
            user=cls.client_user,
            client_type=Customer.ClientType.NATURAL,
            account='1234567890123456',
            agency_bank='BANDEC',
            address='Addr',
            phone='12345678',
        )

    def _make_sub(self, status, title_suffix, payment_method='transfer'):
        service = Service.objects.create(
            user=self.provider,
            title=f'Servicio {title_suffix}',
            summary=f'Sum {title_suffix}',
            service_type=Service.COMMERCIAL,
            price=10,
        )
        return ServiceSubscription.objects.create(
            customer=self.customer,
            service=service,
            start_date=timezone.now() - timedelta(days=30),
            payment_status=status,
            payment_method=payment_method,
        )

    def _make_orphan_invoice(self, sub):
        """Replica `process_batch_invoice`: factura sin ancla, línea con la
        suscripción. Es la forma en que quedan realmente en la base."""
        invoice = Invoice.objects.create(
            customer=self.customer,
            subscription=None,
            number=f'2026-{Invoice.objects.count() + 1:04d}',
            issue_date=timezone.now().date(),
            amount=10,
            pdf=SimpleUploadedFile('f.pdf', b'%PDF-1.4 fake', content_type='application/pdf'),
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            subscription=sub,
            codigo=sub.service.code or '',
            descripcion=sub.service.title,
            cantidad=1,
            unidad_medida='DÍA',
            precio=10,
            importe=10,
        )
        return invoice

    def test_pending_shows_invoice_button_for_manual_invoice(self):
        """D1: la factura cuelga del `InvoiceItem`, no del ancla de la factura.

        La facturación por lote crea la factura con `subscription = NULL` y
        cada línea apunta a su suscripción, así que buscarla sólo por
        `Invoice.subscription` devolvía `None` y el botón "Ver factura" no se
        renderizaba: la tarjeta "pendiente de pago" salía con el bloque de
        acciones vacío. El admin sí la veía porque su listado no pasa por la
        suscripción.
        """
        sub = self._make_sub('pending', 'manual-invoice')
        invoice = self._make_orphan_invoice(sub)
        self.client.force_login(self.client_user)
        html = self.client.get(reverse('home:services_commercial')).content.decode()
        self.assertIn('Ver factura', html)
        self.assertIn(
            reverse('commercial:factura_download', args=[invoice.uuid]),
            html,
        )

    def test_subscription_does_not_show_another_services_invoice(self):
        """Cada suscripción ve SÓLO la factura de su propia línea.

        Filtrar por cliente encajaba cualquier factura manual del mismo cliente
        en cualquier tarjeta: con dos servicios y dos facturas, la suscripción
        de un servicio recibía el botón de descarga del otro.
        """
        sub_a = self._make_sub('pending', 'servicio-a')
        sub_b = self._make_sub('pending', 'servicio-b')
        invoice_a = self._make_orphan_invoice(sub_a)
        invoice_b = self._make_orphan_invoice(sub_b)

        view = CommercialServicesListView()
        view.request = RequestFactory().get('/')
        view.request.user = self.client_user
        resolved = {s.pk: s.latest_invoice_uuid for s in view.get_queryset()}

        self.assertEqual(resolved[sub_a.pk], invoice_a.uuid)
        self.assertEqual(resolved[sub_b.pk], invoice_b.uuid)
        self.assertNotEqual(resolved[sub_a.pk], invoice_b.uuid)

    def test_cancelled_manual_invoice_is_not_offered(self):
        """Una factura anulada no es pagable, así que no se ofrece el botón."""
        self._make_sub('pending', 'cancelled-invoice')
        Invoice.objects.create(
            customer=self.customer,
            subscription=None,
            issue_date=timezone.now().date(),
            amount=10,
            is_cancelled=True,
            pdf=SimpleUploadedFile('f.pdf', b'%PDF-1.4 fake', content_type='application/pdf'),
        )
        self.client.force_login(self.client_user)
        html = self.client.get(reverse('home:services_commercial')).content.decode()
        self.assertNotIn('Ver factura', html)

    def test_lists_all_subscription_states_in_priority_order(self):
        # 'expired' ya no es un payment_status: la baja lógica produce
        # status_display == 'cancelada' y el queryset de Home excluye las
        # suscripciones con record_active=False, así que sólo quedan tres
        # estados visibles (solicitado, pendiente, pagado).
        self._make_sub('paid', 'pagado')
        self._make_sub('pending', 'pendiente')
        self._make_sub('requested', 'solicitado')
        self.client.force_login(self.client_user)
        html = self.client.get(reverse('home:services_commercial')).content.decode()
        self.assertIn('Servicio solicitado', html)
        self.assertIn('Servicio pendiente', html)
        self.assertIn('Servicio pagado', html)
        # El orden Case/When: requested(0) -> pending(1) -> paid(2).
        positions = [
            html.index('Servicio solicitado'),
            html.index('Servicio pendiente'),
            html.index('Servicio pagado'),
        ]
        self.assertEqual(positions, sorted(positions))

    def test_ribbon_class_and_label_per_subscription_state(self):
        # REQ-03: el ribbon se resuelve vía status_ribbon|get_item:status_display
        # (pagado -> bg-green, pendiente -> bg-orange, solicitado -> bg-blue,
        # cancelada -> bg-red); nunca hardcodeado.
        self._make_sub('requested', 'ribbon-solicitado')
        self._make_sub('pending', 'ribbon-pendiente')
        self._make_sub('paid', 'ribbon-pagado')
        # Una suscripción dada de baja (baja lógica) queda en 'cancelada' pero
        # NO se renderiza: el listado de Home filtra record_active=True.
        cancelada = self._make_sub('requested', 'ribbon-cancelada')
        cancelada.delete()
        self.assertEqual(cancelada.status_display, 'cancelada')
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('home:services_commercial'))
        html = response.content.decode()
        self.assertEqual(
            response.context['status_ribbon'],
            {
                'pagado': 'bg-green',
                'pendiente': 'bg-orange',
                'solicitado': 'bg-blue',
                'cancelada': 'bg-red',
            },
        )
        # Un ribbon por card activa, con la clase y el texto del estado correctos.
        self.assertEqual(html.count('ribbon-bookmark'), 3)
        self.assertIn('ribbon-bookmark bg-green">pagado', html)
        self.assertIn('ribbon-bookmark bg-orange">pendiente', html)
        self.assertIn('ribbon-bookmark bg-blue">solicitado', html)
        # La cancelada no aparece en Home (soft delete la saca del queryset).
        self.assertNotIn('ribbon-cancelada', html)

    def test_calendar_icon_precedes_date_range_in_dom(self):
        # REQ-05: el icono de calendario aparece antes del rango de fechas en
        # el DOM del card (mismo formato d/m/Y que el template).
        subscription = self._make_sub('paid', 'orden-calendario')
        self.client.force_login(self.client_user)
        html = self.client.get(reverse('home:services_commercial')).content.decode()
        start_label = django_date_filter(subscription.start_date, 'd/m/Y')
        self.assertIn('ti-calendar', html)
        self.assertIn(start_label, html)
        self.assertLess(html.index('ti-calendar'), html.index(start_label))

    def test_metadata_layout_order_is_dates_category_period_payment_price(self):
        # REQ-05 S3: el bloque metadata del card Mis Servicios respeta el orden
        # DOM fechas (ti-calendar, "Vigencia:") -> categoría (ti-tag) -> período
        # de facturación (ti-calendar-event, "Período:") -> método de pago
        # (payment_method_icon) -> precio (format_cup, solo monto). El scope a
        # la región metadata evita colisiones con el menú (ti-building-bank
        # también está en "Institución").
        subscription = self._make_sub('paid', 'orden-metadata')
        Invoice.objects.create(subscription=subscription, number='F001-003', amount=10)
        self.client.force_login(self.client_user)
        html = self.client.get(reverse('home:services_commercial')).content.decode()
        meta_start = html.index('d-flex flex-column flex-grow-1 text-secondary mb-3')
        meta_end = html.index('justify-content-end gap-2', meta_start)
        meta_html = html[meta_start:meta_end]
        dates_marker = meta_html.index('ti-calendar')
        category_marker = meta_html.index('ti-tag')
        period_marker = meta_html.index('ti-calendar-event')
        payment_marker = meta_html.index('ti-building-bank')
        price_marker = meta_html.index('$10,00')
        self.assertLess(dates_marker, category_marker)
        self.assertLess(category_marker, period_marker)
        self.assertLess(period_marker, payment_marker)
        self.assertLess(payment_marker, price_marker)
        self.assertNotIn('ti-calendar-month', meta_html)
        self.assertNotIn('d-flex flex-wrap gap-2', meta_html)
        self.assertNotIn('CUP/', meta_html)

    def test_subscription_lines_have_strong(self):
        # La línea de fechas usa "Inicio:" con la fecha de arranque en <strong>
        # (d/m/Y). Ya no hay rango: la suscripción no vence, así que no existe
        # una segunda fecha que acotar el período. La línea de período de
        # facturación (ti-calendar-event) sigue mostrando el período facturado;
        # la línea de categoría (ti-tag) usa <strong> con
        # get_service_category_display (patrón de service_detail).
        subscription = self._make_sub('paid', 'metadatos-strong')
        self.client.force_login(self.client_user)
        html = self.client.get(reverse('home:services_commercial')).content.decode()
        start_label = django_date_filter(subscription.start_date, 'd/m/Y')
        self.assertIn('ti-calendar-event', html)
        self.assertIn('Período: <strong>1 día</strong>', html)
        self.assertIn(f'Inicio: <strong>{start_label}</strong>', html)
        self.assertIn('Categoría: <strong>Pronóstico</strong>', html)

    def test_subscription_payment_icon_presencial(self):
        # REQ-05 S5 (variante presencial): el icono ti-building-store con me-1
        # aparece ANTES del texto "Pago Presencial" en su línea <div class="mb-2">.
        self._make_sub('paid', 'pago-presencial', payment_method='presencial')
        self.client.force_login(self.client_user)
        html = self.client.get(reverse('home:services_commercial')).content.decode()
        payment_marker = html.index('Pago Presencial')
        line_start = html.rfind('<div class="mb-2">', 0, payment_marker)
        line_end = html.index('</div>', payment_marker)
        payment_line = html[line_start:line_end]
        self.assertIn('ti ti-building-store', payment_line)
        self.assertLess(payment_line.index('me-1'), payment_line.index('Pago Presencial'))

    def test_subscription_no_payment_method_omits_line(self):
        # REQ-05 S6: sin payment_method la línea de método de pago NO se
        # renderiza; las demás líneas de metadata siguen presentes.
        self._make_sub('paid', 'sin-pago', payment_method=None)
        self.client.force_login(self.client_user)
        html = self.client.get(reverse('home:services_commercial')).content.decode()
        meta_start = html.index('d-flex flex-column flex-grow-1 text-secondary mb-3')
        meta_end = html.index('justify-content-end gap-2', meta_start)
        meta_html = html[meta_start:meta_end]
        for icon in ('ti-qrcode', 'ti-building-bank', 'ti-building-store', 'ti-credit-card'):
            self.assertNotIn(icon, meta_html)
        self.assertIn('ti-calendar', meta_html)
        self.assertIn('Categoría:', meta_html)
        self.assertIn('Período:', meta_html)

    def test_subscription_commercial_only_price_highlight(self):
        # REQ-05 S7: solo servicios COMMERCIAL muestran precio destacado; una
        # sub cuyo service es PUBLIC no renderiza display-6 pero sí las líneas
        # de fechas y categoría.
        service = Service.objects.create(
            user=self.provider,
            title='Servicio público sub',
            summary='Sum público',
            service_type=Service.PUBLIC,
        )
        subscription = ServiceSubscription.objects.create(
            customer=self.customer,
            service=service,
            start_date=timezone.now() - timedelta(days=30),
            payment_status='paid',
            payment_method='transfer',
        )
        self.client.force_login(self.client_user)
        html = self.client.get(reverse('home:services_commercial')).content.decode()
        meta_start = html.index('d-flex flex-column flex-grow-1 text-secondary mb-3')
        meta_end = html.index('justify-content-end gap-2', meta_start)
        meta_html = html[meta_start:meta_end]
        start_label = django_date_filter(subscription.start_date, 'd/m/Y')
        self.assertNotIn('display-6', meta_html)
        self.assertIn('ti-calendar', meta_html)
        self.assertIn(f'Inicio: <strong>{start_label}</strong>', meta_html)

    def test_subscription_price_no_suffix(self):
        # REQ-05 S2: el precio destacado es SOLO el monto format_cup, sin el
        # sufijo "CUP/<período>" (en Mis Servicios la línea de período de
        # facturación aparece antes del precio).
        self._make_sub('paid', 'precio-sin-sufijo')
        self.client.force_login(self.client_user)
        html = self.client.get(reverse('home:services_commercial')).content.decode()
        meta_start = html.index('d-flex flex-column flex-grow-1 text-secondary mb-3')
        meta_end = html.index('justify-content-end gap-2', meta_start)
        meta_html = html[meta_start:meta_end]
        self.assertIn('display-6 fw-bold text-primary', meta_html)
        self.assertIn('$10,00', meta_html)
        self.assertNotIn('CUP/', meta_html)
        self.assertLess(meta_html.index('Período:'), meta_html.index('display-6'))

    def test_subscription_price_shows_total_to_pay(self):
        # El precio destacado muestra el TOTAL a pagar = precio × cantidad.
        sub = self._make_sub('paid', 'total-a-pagar')
        sub.quantity = 3
        sub.save()
        self.client.force_login(self.client_user)
        html = self.client.get(reverse('home:services_commercial')).content.decode()
        meta_start = html.index('d-flex flex-column flex-grow-1 text-secondary mb-3')
        meta_end = html.index('justify-content-end gap-2', meta_start)
        meta_html = html[meta_start:meta_end]
        self.assertIn('display-6 fw-bold text-primary', meta_html)
        self.assertIn('$30,00', meta_html)


class CommercialServicesListContextualActionsTests(TestCase):
    """mis-servicios-cliente REQ-04 — acciones contextuales por estado en Mis
    Servicios: pending+qr -> "Ver factura" + "Pagar con QR"; pending otro ->
    solo factura; requested -> badge "En proceso" sin botones."""

    @classmethod
    def setUpTestData(cls):
        _disable_maintenance_mode()
        cls.provider = User.objects.create_user(
            'ctxprov', 'ctxprov@test.com', 'pass', first_name='P', last_name='V'
        )
        cls.client_user = User.objects.create_user(
            'ctxcli', 'ctxcli@test.com', 'pass', first_name='C', last_name='V'
        )
        cls.customer = Customer.objects.create(
            user=cls.client_user,
            client_type=Customer.ClientType.NATURAL,
            account='1234567890123456',
            agency_bank='BANDEC',
            address='Addr',
            phone='12345678',
        )

    def _sub(self, status, payment_method='transfer'):
        service = Service.objects.create(
            user=self.provider,
            title=f'Servicio {status}-{payment_method}',
            summary='Sum',
            service_type=Service.COMMERCIAL,
            price=10,
        )
        return ServiceSubscription.objects.create(
            customer=self.customer,
            service=service,
            start_date=timezone.now() - timedelta(days=1),
            payment_status=status,
            payment_method=payment_method,
        )

    def _html(self):
        self.client.force_login(self.client_user)
        return self.client.get(reverse('home:services_commercial')).content.decode()

    def test_paid_subscription_keeps_invoice_and_certificate_both_visible(self):
        """Los documentos son ACUMULATIVOS: pagar no borra la factura.

        Antes la rama `is_active` del template mostraba sólo el certificado y
        la factura desaparecía del card justo cuando el cliente la necesitaba
        como respaldo. Ahora ambos botones se renderizan por separado.
        """
        sub = self._sub('paid')
        invoice = Invoice.objects.create(
            subscription=sub,
            number='F002-001',
            amount=10,
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            subscription=sub,
            descripcion='Servicio',
            cantidad=Decimal('1'),
            precio=Decimal('10.00'),
        )
        certificate = Certificate.objects.create(
            subscription=sub,
            pdf='certificate_pdfs/cert-paid.pdf',
        )
        html = self._html()
        self.assertIn('Ver factura', html)
        self.assertIn(f'factura/{invoice.uuid}/pdf/?inline=1', html)
        self.assertIn('Ver certificado', html)
        self.assertIn(
            f'certificado/{certificate.uuid}/pdf/?inline=1',
            html,
        )

    def test_paid_subscription_without_certificate_says_so(self):
        sub = self._sub('paid')
        invoice = Invoice.objects.create(subscription=sub, number='F002-002', amount=10)
        InvoiceItem.objects.create(
            invoice=invoice,
            subscription=sub,
            descripcion='Servicio',
            cantidad=Decimal('1'),
            precio=Decimal('10.00'),
        )
        html = self._html()
        self.assertIn('Ver factura', html)
        self.assertIn('Sin certificado', html)

    def test_pending_qr_offers_invoice_and_qr_payment(self):
        sub = self._sub('pending', payment_method='qr')
        invoice = Invoice.objects.create(
            subscription=sub,
            number='F001-001',
            amount=10,
        )
        html = self._html()
        self.assertIn('Ver factura', html)
        self.assertIn(f'factura/{invoice.uuid}/pdf/?inline=1', html)
        self.assertIn('ti-qrcode', html)
        self.assertIn('Pagar con QR', html)
        self.assertIn(reverse('home:payment'), html)

    def test_pending_transfer_offers_invoice_without_qr(self):
        sub = self._sub('pending', payment_method='transfer')
        invoice = Invoice.objects.create(
            subscription=sub,
            number='F001-002',
            amount=10,
        )
        html = self._html()
        self.assertIn('Ver factura', html)
        self.assertIn(f'factura/{invoice.uuid}/pdf/?inline=1', html)
        self.assertIn('ti-building-bank', html)
        self.assertNotIn('Pagar con QR', html)
        self.assertNotIn(reverse('home:payment'), html)

    def test_requested_shows_progress_badge_without_action_buttons(self):
        self._sub('requested')
        html = self._html()
        self.assertIn('En proceso', html)
        self.assertNotIn('Ver factura', html)
        self.assertNotIn('Pagar con QR', html)
        self.assertNotIn('Ver PDF', html)
        self.assertNotIn('ti ti-send', html)

    def test_subscription_payment_icon_qr(self):
        self._sub('pending', payment_method='qr')
        html = self._html()
        self.assertIn('ti-qrcode', html)
        self.assertNotIn('ti-credit-card', html)

    def test_subscription_payment_icon_transfer(self):
        self._sub('pending', payment_method='transfer')
        html = self._html()
        self.assertIn('ti-building-bank', html)
        self.assertNotIn('ti-credit-card', html)

    def test_subscription_no_dollar_icon_in_price(self):
        self._sub('pending', payment_method='qr')
        html = self._html()
        self.assertNotIn('ti-currency-dollar', html)

    def test_pending_subscription_without_invoice_hides_invoice_button(self):
        # REQ-04 S2: pending+qr SIN facturas -> el botón "Ver factura" (y su
        # URL factura_download) NO se renderiza; el card sigue ofreciendo
        # "Pagar con QR" (la ausencia no es un fallo de renderizado del estado).
        self._sub('pending', payment_method='qr')
        html = self._html()
        self.assertNotIn('Ver factura', html)
        self.assertNotIn('/factura/', html)
        self.assertNotIn('ti ti-receipt', html)
        self.assertIn('Pagar con QR', html)
        self.assertIn(reverse('home:payment'), html)
        self.assertIn('ti-qrcode', html)


class ServicesCommercialStaffButtonTests(TestCase):
    """staff/management buttons on the public commercial view."""

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

    def _get_page(self, **query):
        return self.client.get(reverse('home:services_commercial_public'), query)

    def test_catalogue_paginated_ten_per_page(self):
        # El catálogo comercial página a 10; con 12 servicios (incluido el
        # anónimo existente) la primera página muestra 10 y la paginación
        # compacta está presente. El orden es lexicográfico por título, así
        # que 'Comercial paginado 8' y '9' quedan fuera de la página 1.
        for index in range(11):
            Service.objects.create(
                user=self.provider,
                title=f'Comercial paginado {index}',
                summary='Sum',
                service_type=Service.COMMERCIAL,
            )
        self.client.logout()
        html = self._get_page().content.decode()
        self.assertIn('Comercial paginado 0', html)
        self.assertIn('Comercial paginado 7', html)
        self.assertNotIn('Comercial paginado 8', html)
        self.assertNotIn('Comercial paginado 9', html)
        self.assertIn('<ul class="pagination pagination-sm', html)
        self.assertIn('Pág. 1 de 2', html)
        # La página 2 trae los restantes.
        page2 = self._get_page(page=2).content.decode()
        self.assertIn('Comercial paginado 8', page2)
        self.assertIn('Comercial paginado 9', page2)
        self.assertNotIn('Comercial paginado 0', page2)

    def test_staff_sees_edit_and_new_service_buttons(self):
        update_url = reverse('commercial:servicio_update', args=[self.anon_service.uuid])
        self.client.force_login(self.staff)
        html = self._get_page().content.decode()
        self.assertIn('Editar', html)
        self.assertIn(update_url, html)
        self.assertIn('Nuevo', html)
        self.assertIn(reverse('commercial:servicio_create'), html)

    def test_staff_without_customer_profile_sees_no_solicitar(self):
        # Un admin autenticado sin perfil Customer no debe ver el botón
        # "Solicitar" en el catálogo: solo los clientes registrados lo ven
        # (mismo umbral que el detail/post de solicitud).
        self.client.force_login(self.staff)
        html = self._get_page().content.decode()
        self.assertIn('Editar', html)
        self.assertNotIn('ti ti-send', html)
        self.assertNotIn('<i class="icon ti ti-login"></i> Iniciar sesión', html)

    def test_anonymous_sees_login_cta_only_and_no_ribbon(self):
        # REQ-06 + delta home-public-services-layout (escenario anónimo): el
        # catálogo muestra un único control "Iniciar sesión" (ti-login), sin
        # botones staff, sin "Solicitar" ni ribbons por estado.
        self.client.logout()
        html = self._get_page().content.decode()
        self.assertNotIn('Editar', html)
        self.assertNotIn('Nuevo', html)
        self.assertNotIn('ti ti-send', html)
        self.assertNotIn('ribbon-bookmark', html)
        self.assertIn('<i class="icon ti ti-login"></i> Iniciar sesión', html)

    def test_pending_non_qr_public_catalog_is_state_neutral(self):
        """REQ-06: la guía 'Ver factura' para pending sin QR vive en Mis Servicios;
        el catálogo público no la renderiza."""
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
        )
        self.client.force_login(client_user)
        html = self._get_page().content.decode()
        self.assertNotIn('Ver factura', html)
        self.assertNotIn('Pendiente de pago', html)
        self.assertNotIn('Solicitar de nuevo', html)
        self.assertIn('Solicitar', html)


class CommercialCatalogCodeAndCategoryUITests(TestCase):
    """commercial-service-categories (delta) — el card público muestra el badge
    de categoría y el código de forma discreta solo si existe; sin `code`, no
    hay etiqueta 'Código:'."""

    @classmethod
    def setUpTestData(cls):
        _disable_maintenance_mode()
        cls.provider = User.objects.create_user(
            'catcodeprov', 'catcodeprov@test.com', 'pass', first_name='P', last_name='C'
        )

    def _catalog_html(self):
        return self.client.get(reverse('home:services_commercial_public')).content.decode()

    def test_catalog_shows_category_badge_and_code(self):
        Service.objects.create(
            user=self.provider,
            title='Servicio con código',
            summary='Sum',
            service_type=Service.COMMERCIAL,
            service_category='agrometeo',
            code='C200',
            price=100,
        )
        html = self._catalog_html()
        self.assertIn('Agrometeorológico', html)
        self.assertNotIn('Código: C200', html)

    def test_catalog_hides_code_label_when_service_has_no_code(self):
        Service.objects.create(
            user=self.provider,
            title='Servicio sin código',
            summary='Sum',
            service_type=Service.COMMERCIAL,
            price=100,
        )
        html = self._catalog_html()
        self.assertNotIn('Código:', html)

    def test_catalog_category_badge_has_tag_icon_pronostico(self):
        Service.objects.create(
            user=self.provider,
            title='Servicio pronóstico',
            summary='Sum',
            service_type=Service.COMMERCIAL,
            service_category='pronostico',
            price=100,
        )
        html = self._catalog_html()
        # Espec: el icono ti-tag con me-1 aparece ANTES del label
        # "Categoría:" en su línea <div class="mb-2">.
        category_marker = html.index('Categoría:')
        line_start = html.rfind('<div class="mb-2">', 0, category_marker)
        line_end = html.index('</div>', category_marker)
        category_line = html[line_start:line_end]
        self.assertIn('ti ti-tag', category_line)
        self.assertLess(category_line.index('me-1'), category_line.index('Categoría:'))
        self.assertIn('<strong>Pronóstico</strong>', category_line)

    def test_catalog_category_badge_has_tag_icon_agrometeo(self):
        Service.objects.create(
            user=self.provider,
            title='Servicio agrometeo',
            summary='Sum',
            service_type=Service.COMMERCIAL,
            service_category='agrometeo',
            price=100,
        )
        html = self._catalog_html()
        # Espec: el icono ti-tag con me-1 aparece ANTES del label
        # "Categoría:" en su línea <div class="mb-2">.
        category_marker = html.index('Categoría:')
        line_start = html.rfind('<div class="mb-2">', 0, category_marker)
        line_end = html.index('</div>', category_marker)
        category_line = html[line_start:line_end]
        self.assertIn('ti ti-tag', category_line)
        self.assertLess(category_line.index('me-1'), category_line.index('Categoría:'))
        self.assertIn('<strong>Agrometeorológico</strong>', category_line)

    def test_catalog_dom_order_category_period_price(self):
        # Escenario "Orden DOM categoría-período-precio": las líneas de la
        # metadata aparecen en orden categoría -> período -> precio, cada una
        # en <div class="mb-2"> independiente y sin bloque d-flex flex-wrap
        # gap-2 apiñado.
        Service.objects.create(
            user=self.provider,
            title='Servicio orden dom',
            summary='Sum',
            service_type=Service.COMMERCIAL,
            service_category='pronostico',
            price=1234.56,
        )
        html = self._catalog_html()
        meta_start = html.index('d-flex flex-column flex-grow-1 text-secondary mb-3')
        meta_end = html.index('justify-content-end gap-2', meta_start)
        meta_html = html[meta_start:meta_end]
        category_marker = meta_html.index('Categoría:')
        period_marker = meta_html.index('Período:')
        price_marker = meta_html.index('$1.234,56')
        self.assertLess(category_marker, period_marker)
        self.assertLess(period_marker, price_marker)
        self.assertNotIn('d-flex flex-wrap gap-2', meta_html)

    def test_catalog_price_uses_display6_highlight(self):
        # Escenario "Precio destacado display-6 con CUP/período": el precio usa
        # display-6 fw-bold text-primary con el monto format_cup y el small
        # text-secondary con "CUP/<período>".
        Service.objects.create(
            user=self.provider,
            title='Servicio precio destacado',
            summary='Sum',
            service_type=Service.COMMERCIAL,
            service_category='agrometeo',
            price=100,
        )
        html = self._catalog_html()
        meta_start = html.index('d-flex flex-column flex-grow-1 text-secondary mb-3')
        meta_end = html.index('justify-content-end gap-2', meta_start)
        meta_html = html[meta_start:meta_end]
        self.assertIn('display-6 fw-bold text-primary', meta_html)
        self.assertIn('$100,00', meta_html)
        self.assertIn('<small class="text-secondary">CUP/mes</small>', meta_html)
        self.assertLess(
            meta_html.index('display-6'),
            meta_html.index('<small class="text-secondary">CUP/mes</small>'),
        )

    def test_catalog_no_currency_dollar_icon(self):
        Service.objects.create(
            user=self.provider,
            title='Servicio sin dollar',
            summary='Sum',
            service_type=Service.COMMERCIAL,
            price=200,
        )
        html = self._catalog_html()
        self.assertNotIn('ti-currency-dollar', html)
        self.assertIn('$200,00', html)


class ServicesVisibilityFilterTests(TestCase):
    """servicios-activacion-filtro-home — servicios desactivados invisibles en el portal.

    Las vistas públicas (listado público, listado comercial y detalle) filtran
    record_active=True; un servicio desactivado no aparece ni en listas ni en
    detalle ni en relacionados.
    """

    @classmethod
    def setUpTestData(cls):
        _disable_maintenance_mode()
        cls.provider = User.objects.create_user(
            'providervis',
            'providervis@test.com',
            'pass',
            first_name='Proveedor',
            last_name='Visibilidad',
        )

    def _make_service(self, title, service_type, active=True):
        kwargs = {
            'user': self.provider,
            'title': title,
            'summary': f'Resumen {title}',
            'service_type': service_type,
        }
        if service_type == Service.COMMERCIAL:
            kwargs['price'] = 100
        service = Service.objects.create(**kwargs)
        if not active:
            service.record_active = False
            service.save(update_fields=['record_active'])
        return service

    def test_inactive_public_service_hidden_from_home_list(self):
        self._make_service('Visibilidad pública activa', Service.PUBLIC)
        self._make_service('Visibilidad pública oculta', Service.PUBLIC, active=False)
        html = self.client.get(reverse('home:services_public')).content.decode()
        self.assertIn('Visibilidad pública activa', html)
        self.assertNotIn('Visibilidad pública oculta', html)

    def test_inactive_commercial_service_hidden_from_home_list(self):
        self._make_service('Visibilidad comercial activa', Service.COMMERCIAL)
        self._make_service('Visibilidad comercial oculta', Service.COMMERCIAL, active=False)
        html = self.client.get(reverse('home:services_commercial_public')).content.decode()
        self.assertIn('Visibilidad comercial activa', html)
        self.assertNotIn('Visibilidad comercial oculta', html)

    def test_inactive_commercial_service_detail_returns_404(self):
        hidden = self._make_service('Detalle oculto', Service.COMMERCIAL, active=False)
        self.client.force_login(self.provider)
        url = reverse('home:services_commercial_detail', args=[hidden.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_related_services_exclude_inactive(self):
        active = self._make_service('Detalle activo', Service.COMMERCIAL)
        self._make_service('Relacionada oculta', Service.COMMERCIAL, active=False)
        self._make_service('Relacionada visible', Service.COMMERCIAL)
        self.client.force_login(self.provider)
        url = reverse('home:services_commercial_detail', args=[active.uuid])
        html = self.client.get(url).content.decode()
        self.assertIn('Relacionada visible', html)
        self.assertNotIn('Relacionada oculta', html)


class ServiceReRequestUiTests(TestCase):
    """reesolicitar-servicio-activo — detail + public list re-request UI."""

    @classmethod
    def setUpTestData(cls):
        _disable_maintenance_mode()
        cls.provider = User.objects.create_user(
            'reerqprov2', 'reerqprov2@test.com', 'pass', first_name='P', last_name='R'
        )
        cls.client_user = User.objects.create_user(
            'reerqclient', 'reerqclient@test.com', 'pass', first_name='C', last_name='L'
        )
        cls.customer = Customer.objects.create(
            user=cls.client_user,
            client_type=Customer.ClientType.NATURAL,
            account='1234567890123456',
            agency_bank='BANDEC',
            address='Addr',
            phone='12345678',
        )
        cls.service = Service.objects.create(
            user=cls.provider,
            title='Re-request Comercial',
            summary='Sum',
            service_type=Service.COMMERCIAL,
            service_category='pronostico',
            price=20,
        )

    def _login(self):
        self.client.force_login(self.client_user)

    def _detail_url(self):
        return reverse('home:services_commercial_detail', args=[self.service.uuid])

    def _make_sub(self, **kwargs):
        defaults = {
            'customer': self.customer,
            'service': self.service,
            'start_date': timezone.now() - timedelta(days=1),
        }
        defaults.update(kwargs)
        return ServiceSubscription.objects.create(**defaults)

    def test_active_paid_renders_form_and_cta(self):
        self._make_sub(payment_status='paid', payment_method='transfer')
        self._login()
        html = self.client.get(self._detail_url()).content.decode()
        self.assertIn('subscription-form', html)
        self.assertIn('Solicitar', html)
        # Sin `end_date` no hay "vigente" que anunciar: la suscripción no vence.
        # El aviso decía que la nueva solicitud se procesaría junto a la
        # vigente, lo cual promete algo que el sistema no coordina.
        self.assertNotIn('Ya tiene este servicio activo', html)
        self.assertNotIn('activa hasta', html)
        self.assertNotIn('la vigente', html)
        self.assertNotIn('Ya tienes una solicitud o suscripción para este servicio.', html)

    def test_cancelled_subscription_no_se_anuncia_como_activa(self):
        """Una baja lógica no borra la fila: sólo la marca.

        Sin filtrar por `record_active` una suscripción anulada seguía
        apareciendo como activa en el detalle.
        """
        sub = self._make_sub(payment_status='paid', payment_method='transfer')
        sub.delete()
        self._login()
        html = self.client.get(self._detail_url()).content.decode()
        self.assertNotIn('Ya tiene este servicio activo', html)
        self.assertIn('subscription-form', html)

    def test_in_flight_still_shows_form(self):
        """B1: una solicitud en vuelo avisa pero no oculta el formulario."""
        self._make_sub(payment_status='requested', payment_method='transfer')
        self._login()
        html = self.client.get(self._detail_url()).content.decode()
        self.assertIn('id="subscription-form"', html)
        self.assertIn('Ya has solicitado este servicio. Estamos procesando tu solicitud.', html)

    def test_in_flight_pending_still_shows_form(self):
        self._make_sub(payment_status='pending', payment_method='transfer')
        self._login()
        html = self.client.get(self._detail_url()).content.decode()
        self.assertIn('id="subscription-form"', html)

    def test_public_list_active_shows_state_neutral_card(self):
        # REQ-06: el catálogo es neutral al estado; sin ribbon ni re-solicitud.
        self._make_sub(payment_status='paid', payment_method='transfer')
        self._login()
        html = self.client.get(reverse('home:services_commercial_public')).content.decode()
        self.assertNotIn('Activo', html)
        self.assertNotIn('Solicitar de nuevo', html)
        self.assertIn('Solicitar', html)
        # Badge de categoría y precio format_cup (fixture pronostico + $20).
        self.assertIn('Pronóstico', html)
        self.assertIn('$20,00', html)

    def test_public_list_requested_shows_single_solicitar(self):
        self._make_sub(payment_status='requested', payment_method='transfer')
        self._login()
        html = self.client.get(reverse('home:services_commercial_public')).content.decode()
        self.assertNotIn('Solicitado', html)
        self.assertNotIn('Solicitar de nuevo', html)
        self.assertIn('Solicitar', html)

    def test_public_list_state_neutral_regardless_of_subscription_state(self):
        self._make_sub(payment_status='paid', payment_method='transfer')
        self._make_sub(payment_status='requested', payment_method='transfer')
        self._login()
        html = self.client.get(reverse('home:services_commercial_public')).content.decode()
        self.assertNotIn('Activo', html)
        self.assertNotIn('Solicitado', html)
        self.assertNotIn('Solicitar de nuevo', html)
        self.assertIn('Solicitar', html)

    def test_detail_renders_action_icons(self):
        # REQ-07: submit "Solicitar" (ti-send) y "Cancelar" (ti-x) presentes en
        # el detail comercial; los relacionados usan el card de catálogo con
        # botón "Solicitar" (ti-send) y metadata completa, sin botón "Ver".
        self._make_sub(payment_status='paid', payment_method='transfer')
        Service.objects.create(
            user=self.provider,
            title='Relacionado iconos',
            summary='Sum relacionado',
            service_type=Service.COMMERCIAL,
            price=5,
        )
        self._login()
        html = self.client.get(self._detail_url()).content.decode()
        self.assertIn('ti ti-send', html)
        self.assertIn('ti ti-x', html)
        self.assertNotIn('ti-eye', html)
        related_pos = html.find('Relacionado iconos')
        self.assertGreater(related_pos, 0)
        self.assertIn('Categoría:', html[related_pos:])
        self.assertIn('Período:', html[related_pos:])
        self.assertIn('CUP/día', html[related_pos:])

    def test_related_services_same_category_only(self):
        """Solo servicios de la misma categoría aparecen en relacionados."""
        Service.objects.create(
            user=self.provider,
            title='Relacionado agrometeo',
            summary='Sum otro',
            service_type=Service.COMMERCIAL,
            service_category='agrometeo',
            price=5,
        )
        Service.objects.create(
            user=self.provider,
            title='Relacionado pronóstico',
            summary='Sum prono',
            service_type=Service.COMMERCIAL,
            service_category='pronostico',
            price=5,
        )
        self._make_sub(payment_status='paid', payment_method='transfer')
        self._login()
        html = self.client.get(self._detail_url()).content.decode()
        self.assertIn('Relacionado pronóstico', html)
        self.assertNotIn('Relacionado agrometeo', html)

    def test_related_services_paginated_three_per_page(self):
        # Los relacionados se muestran de a 3 (una fila col-lg-4); con más
        # servicios, la primera página muestra solo 3 y existe paginación que
        # preserva el resto de la URL del detail.
        for index in range(4):
            Service.objects.create(
                user=self.provider,
                title=f'Relacionado paginado {index}',
                summary='Sum pag',
                service_type=Service.COMMERCIAL,
                service_category='pronostico',
                price=5,
            )
        self._make_sub(payment_status='paid', payment_method='transfer')
        self._login()
        url = self._detail_url()
        html = self.client.get(url).content.decode()
        for index in range(3):
            self.assertIn(f'Relacionado paginado {index}', html)
        self.assertNotIn('Relacionado paginado 3', html)
        self.assertIn('related_page=2', html)
        # La página 2 trae el cuarto y ninguno de la primera página.
        page2 = self.client.get(url, {'related_page': 2}).content.decode()
        self.assertIn('Relacionado paginado 3', page2)
        self.assertNotIn('Relacionado paginado 0', page2)

    def test_related_services_staff_sees_edit_and_new_buttons(self):
        # El staff sin perfil Customer ve en los relacionados los controles del
        # catálogo (Editar/Nuevo) y NUNCA "Solicitar" (igual que la lista
        # comercial pública): la solicitud es exclusiva de clientes registrados.
        Service.objects.create(
            user=self.provider,
            title='Relacionado staff',
            summary='Sum staff',
            service_type=Service.COMMERCIAL,
            service_category='pronostico',
            price=5,
        )
        self._make_sub(payment_status='paid', payment_method='transfer')
        staff = User.objects.create_user(
            'staffdetail',
            'staffdetail@test.com',
            'pass',
            is_staff=True,
            first_name='Staff',
            last_name='Detail',
        )
        self.client.force_login(staff)
        response = self.client.get(self._detail_url())
        html = response.content.decode()
        related_pos = html.find('Relacionado staff')
        self.assertGreater(related_pos, 0)
        related_html = html[related_pos:]
        self.assertIn('ti ti-edit', related_html)
        self.assertIn('ti ti-plus', related_html)
        self.assertIn('Editar', related_html)
        self.assertIn('Nuevo', related_html)
        # Sin commercial_customer el form del detalle no se renderiza y no hay
        # botón Solicitar (ni submit ni card).
        self.assertNotIn('ti ti-send', html)
        self.assertNotIn('subscription-form', html)

    def test_detail_metadata_after_summary_before_author(self):
        """La metadata (Categoría/Período/Precio) sale después del resumen y antes del autor."""
        self._make_sub(payment_status='paid', payment_method='transfer')
        self._login()
        html = self.client.get(self._detail_url()).content.decode()
        summary_pos = html.find('Sum')
        category_pos = html.find('Categoría')
        author_pos = html.find('Publicado por:')
        self.assertGreater(summary_pos, 0)
        self.assertGreater(category_pos, summary_pos)
        self.assertGreater(author_pos, category_pos)

    def test_detail_date_field_uses_tempus(self):
        """El campo de fecha usa el datepicker Tempus Dominus."""
        self._make_sub(payment_status='paid', payment_method='transfer')
        self._login()
        html = self.client.get(self._detail_url()).content.decode()
        self.assertIn('data-tempus="date"', html)
        self.assertNotIn('type="date"', html)

    def test_detail_payment_method_uses_selectgroup(self):
        """El método de pago se renderiza como selectgroup con radios e iconos."""
        self._make_sub(payment_status='paid', payment_method='transfer')
        self._login()
        html = self.client.get(self._detail_url()).content.decode()
        self.assertIn('form-selectgroup', html)
        self.assertIn('ti-qrcode', html)
        self.assertIn('ti-building-bank', html)
        self.assertIn('ti-building-store', html)
        self.assertNotIn('<select', html)

    def test_detail_action_buttons_dashboard_style(self):
        """Los botones de acción usan el patrón de formularios del dashboard."""
        self._make_sub(payment_status='paid', payment_method='transfer')
        self._login()
        html = self.client.get(self._detail_url()).content.decode()
        self.assertIn('d-flex justify-content-end gap-2 pt-3 mt-3 border-top', html)


class MisServiciosMenuItemTests(TestCase):
    """mis-servicios-cliente — el item 'Mis Servicios' del menú es visible con
    CUALQUIER estado de suscripción (requested/pending/paid/expired), no solo
    con pagadas activas (condición `or` de los 4 contadores en menu-list.html)."""

    @classmethod
    def setUpTestData(cls):
        _disable_maintenance_mode()
        cls.provider = User.objects.create_user(
            'menuitemprov', 'menuitemprov@test.com', 'pass', first_name='P', last_name='M'
        )
        cls.client_user = User.objects.create_user(
            'menuitemcli', 'menuitemcli@test.com', 'pass', first_name='C', last_name='M'
        )
        cls.customer = Customer.objects.create(
            user=cls.client_user,
            client_type=Customer.ClientType.NATURAL,
            account='1234567890123456',
            agency_bank='BANDEC',
            address='Addr',
            phone='12345678',
        )
        cls.service = Service.objects.create(
            user=cls.provider,
            title='Servicio menú',
            summary='Sum',
            service_type=Service.COMMERCIAL,
            price=10,
        )

    def _sub(self, status, **kwargs):
        defaults = {
            'customer': self.customer,
            'service': self.service,
            'start_date': timezone.now() - timedelta(days=30),
            'payment_status': status,
            'payment_method': 'transfer',
        }
        defaults.update(kwargs)
        return ServiceSubscription.objects.create(**defaults)

    def _menu_html(self):
        # Cualquier página con layouts/home.html renderiza el menú; la lista
        # pública de servicios es la más liviana.
        return self.client.get(reverse('home:services_public')).content.decode()

    def _menu_item_regex(self):
        # El item real del menú: un <a class="dropdown-item" href="..."> cuya
        # etiqueta visible es "Mis Servicios". El comentario HTML con el mismo
        # texto se renderiza SIEMPRE en el template, así que asertar el label
        # suelto daría falsos positivos (anónimo con item oculto).
        url = reverse('home:services_commercial')
        return re.compile(
            rf'<a class="dropdown-item[^"]*"[^>]*href="{re.escape(url)}"[^>]*>\s*Mis Servicios'
        )

    def test_menu_shows_mis_servicios_with_requested_subscription(self):
        self._sub('requested')
        self.client.force_login(self.client_user)
        html = self._menu_html()
        self.assertRegex(html, self._menu_item_regex())

    def test_menu_shows_mis_servicios_with_pending_subscription(self):
        self._sub('pending')
        self.client.force_login(self.client_user)
        html = self._menu_html()
        self.assertRegex(html, self._menu_item_regex())

    def test_menu_shows_mis_servicios_with_paid_subscription(self):
        self._sub('paid')
        self.client.force_login(self.client_user)
        html = self._menu_html()
        self.assertRegex(html, self._menu_item_regex())

    def test_menu_shows_mis_servicios_with_ancient_subscription(self):
        """El enlace aparece con cualquier suscripción, no con estados sueltos.

        Antes la condición enumeraba `active/requested/pending` y existía sólo
        porque `payment_status='expired'` se escribía a mano en los tests: en
        producción la suspendida nunca se guardaba. Ahora manda el total.

        Este caso usaba una suscripción con el periodo vencido para provar que
        el enlace no dependía de la vigencia. Sin `end_date` no hay periodo que
        venza: la antigüedad es ahora el caso más fuerte de esa misma idea, así
        que se prueba con una suscripción de hace una década.
        """
        self._sub('paid', start_date=timezone.now() - timedelta(days=3650))
        self.client.force_login(self.client_user)
        html = self._menu_html()
        self.assertRegex(html, self._menu_item_regex())

    def test_menu_badge_replaces_animated_dot_when_pending_actions(self):
        # REQ-09 + REQ-10: requested+pending -> badge "2" en Mis Servicios y
        # badge bg-red-lt con total en el toggle padre Servicios; el dot
        # animado desaparece a favor del badge.
        self._sub('requested')
        self._sub('pending')
        self.client.force_login(self.client_user)
        html = self._menu_html()
        self.assertNotIn('status-dot status-dot-animated', html)
        self.assertIn('<span class="badge bg-red-lt ms-2">2</span>', html)
        self.assertIn('<span class="badge bg-blue-lt ms-2">1</span>', html)
        self.assertIn('<span class="badge bg-orange-lt ms-2">1</span>', html)

    def test_menu_dot_animated_hidden_without_pending_actions(self):
        # REQ-10: con solo subs activas (requested+pending = 0) ni dot ni badge
        # bg-red-lt en el toggle padre; el item Mis Servicios sigue visible.
        self._sub('paid')
        self.client.force_login(self.client_user)
        html = self._menu_html()
        self.assertNotIn('status-dot status-dot-animated', html)
        self.assertNotIn('badge bg-red-lt ms-2', html)
        self.assertNotIn('badge bg-orange ms-2', html)
        self.assertRegex(html, self._menu_item_regex())

    def test_services_commercial_menu_item_has_no_state_badges(self):
        # REQ-09 S4: con contadores > 0 (requested+pending) el item "Servicios
        # Comerciales" NO renderiza badges de estado; los badges bg-blue-lt /
        # bg-orange-lt viven SOLO en "Mis Servicios". El scope al anchor real
        # del item evita que un badge duplicado pase desapercibido.
        self._sub('requested')
        self._sub('pending')
        self.client.force_login(self.client_user)
        html = self._menu_html()
        commercial_url = reverse('home:services_commercial_public')
        anchor_start = html.index(f'href="{commercial_url}"')
        anchor_end = html.index('</a>', anchor_start)
        commercial_item = html[anchor_start:anchor_end]
        self.assertNotIn('badge', commercial_item)
        self.assertNotIn('bg-blue-lt', commercial_item)
        self.assertNotIn('bg-orange-lt', commercial_item)
        # Triangulación: los contadores existen y los badges SÍ aparecen en
        # "Mis Servicios" — la ausencia es específica del item Comerciales.
        self.assertIn('<span class="badge bg-blue-lt ms-2">1</span>', html)
        self.assertIn('<span class="badge bg-orange-lt ms-2">1</span>', html)
        self.assertEqual(html.count('badge bg-blue-lt ms-2'), 1)
        self.assertEqual(html.count('badge bg-orange-lt ms-2'), 1)

    def test_menu_hides_mis_servicios_for_anonymous_user(self):
        html = self._menu_html()
        self.assertNotRegex(html, self._menu_item_regex())


class ErrorPagesHistoryBackTests(TestCase):
    """error-pages-history-back — 400/403/404/500 pages have a button with
    history.back() + href fallback to home:index."""

    def test_error_404_has_history_back(self):
        response = self.client.get('/url-que-no-existe-404/')
        html = response.content.decode()
        self.assertIn('history.back()', html)
        self.assertIn('window.history.length>1', html)

    def test_error_403_template_has_history_back(self):
        """Verify 403.html template contains history.back() onclick."""
        from pathlib import Path

        templates_dir = Path(__file__).resolve().parents[3] / 'templates' / 'layouts'
        content = (templates_dir / '403.html').read_text()
        self.assertIn('history.back()', content)
        self.assertIn('window.history.length>1', content)

    def test_error_pages_template_has_history_back(self):
        """Verify all error templates contain the history.back() onclick."""
        from pathlib import Path

        templates_dir = Path(__file__).resolve().parents[3] / 'templates' / 'layouts'
        for name in ('400.html', '403.html', '404.html', '500.html'):
            content = (templates_dir / name).read_text()
            self.assertIn('history.back()', content, f'{name} missing history.back()')
            self.assertIn(
                'window.history.length>1', content, f'{name} missing history.length guard'
            )
