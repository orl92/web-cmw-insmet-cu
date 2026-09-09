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

    def _make_sub(self, status, title_suffix):
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
            end_date=timezone.now() + timedelta(days=30),
            payment_status=status,
            payment_method='transfer',
        )

    def test_lists_all_subscription_states_in_priority_order(self):
        self._make_sub('expired', 'expirado')
        self._make_sub('paid', 'activo')
        self._make_sub('pending', 'pendiente')
        self._make_sub('requested', 'solicitado')
        self.client.force_login(self.client_user)
        html = self.client.get(reverse('home:services_commercial')).content.decode()
        self.assertIn('Servicio solicitado', html)
        self.assertIn('Servicio pendiente', html)
        self.assertIn('Servicio activo', html)
        self.assertIn('Servicio expirado', html)
        # El orden Case/When: requested(0) -> pending(1) -> paid(2) -> expired(3).
        positions = [
            html.index('Servicio solicitado'),
            html.index('Servicio pendiente'),
            html.index('Servicio activo'),
            html.index('Servicio expirado'),
        ]
        self.assertEqual(positions, sorted(positions))


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
        self.assertIn('Nuevo', html)
        self.assertIn(reverse('commercial:servicio_create'), html)

    def test_anonymous_sees_no_management_buttons(self):
        self.client.logout()
        html = self._get_page().content.decode()
        self.assertNotIn('Editar', html)
        self.assertNotIn('Nuevo', html)

    def test_pending_non_qr_public_catalog_is_state_neutral(self):
        """REQ-06: la guía 'Ver factura' para pending sin QR vive en Mis Servicios
        (template de la fase 3); el catálogo público no la renderiza."""
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
        self.assertNotIn('Ver factura', html)
        self.assertNotIn('Pendiente de pago', html)
        self.assertNotIn('Solicitar de nuevo', html)
        self.assertIn('Solicitar', html)


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
            'end_date': timezone.now() + timedelta(days=30),
        }
        defaults.update(kwargs)
        return ServiceSubscription.objects.create(**defaults)

    def test_active_paid_renders_form_and_cta(self):
        self._make_sub(payment_status='paid', payment_method='transfer')
        self._login()
        html = self.client.get(self._detail_url()).content.decode()
        self.assertIn('subscription-form', html)
        self.assertIn('Solicitar', html)
        self.assertIn('activa hasta', html)
        self.assertNotIn('Ya tienes una solicitud o suscripción para este servicio.', html)

    def test_in_flight_hides_form_and_button(self):
        self._make_sub(payment_status='requested', payment_method='transfer')
        self._login()
        html = self.client.get(self._detail_url()).content.decode()
        self.assertNotIn('id="subscription-form"', html)
        self.assertNotIn('type="submit"', html)
        self.assertIn('Ya has solicitado este servicio. Estamos procesando tu solicitud.', html)

    def test_in_flight_pending_hides_form(self):
        self._make_sub(payment_status='pending', payment_method='transfer')
        self._login()
        html = self.client.get(self._detail_url()).content.decode()
        self.assertNotIn('id="subscription-form"', html)
        self.assertNotIn('type="submit"', html)

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
            'end_date': timezone.now() + timedelta(days=30),
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

    def test_menu_shows_mis_servicios_with_expired_subscription(self):
        self._sub('expired', end_date=timezone.now() - timedelta(days=1))
        self.client.force_login(self.client_user)
        html = self._menu_html()
        self.assertRegex(html, self._menu_item_regex())

    def test_menu_hides_mis_servicios_for_anonymous_user(self):
        html = self._menu_html()
        self.assertNotRegex(html, self._menu_item_regex())
