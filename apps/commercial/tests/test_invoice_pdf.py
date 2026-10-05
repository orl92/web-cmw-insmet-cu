"""El PDF de la factura tiene que poder generarse.

`generate_invoice_pdf_standalone` renderiza un template por ruta y después lo
convierte a PDF con `weasyprint.HTML(...).write_pdf()`. Hay dos cosas que este
archivo fija:

1. Que el HTML se arma bien, o sea que la ruta del template existe y el contexto
   le sirve. La ruta quedó apuntando a `factura_template.html` cuando la
   reestructuración de templates (1043f55) renombró el archivo a `template.html`:
   el resultado era `TemplateDoesNotExist` SIEMPRE, sin importar el motor de
   PDF. Con eso, la tarea del worker moría antes de enviar el correo y el
   fallback "Ver PDF" del listado absorbía la excepción y dejaba el PDF vacío.
2. Que el preflight corra antes de escribir, así una máquina sin la pila de
   Pango/Harfbuzz no deja una factura con un PDF a medio escribir.

Historia: acá antes renderizaba `pdfkit`, un wrapper del binario `wkhtmltopdf`,
y el preflight se limitaba a `shutil.which`. Con WeasyPrint el chequeo prueba el
render real (ver `require_pdf_renderer`), porque el fallo de una pila de sistema
ausente es un error profundo y no un `ImportError`.

El render se parchea en el módulo bajo prueba (`invoice_utils.HTML`) para no
depender de la pila de Pango en el test; lo que se fija acá es el HTML, no la
calidad del PDF.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from apps.commercial.models import (
    Contract,
    Customer,
    Invoice,
    InvoiceItem,
    Service,
    ServiceSubscription,
)
from apps.commercial.tests.factories import natural_customer
from apps.commercial.views.invoice_utils import generate_invoice_pdf_standalone
from apps.core.models import CompanySettings

# El parche va donde se usa (el modulo bajo prueba), no donde se llama.
HTML = 'apps.commercial.views.invoice_utils.HTML'
PREFLIGHT = 'apps.commercial.views.invoice_utils.require_pdf_renderer'


def renderizador_ok():
    """El preflight se pasa por alto: simula que la pila de Pango funciona."""
    return patch(PREFLIGHT, return_value=None)


def pdf_stub():
    """Captura el HTML que se le pasa a WeasyPrint y devuelve bytes de PDF."""
    stub = patch(HTML, autospec=True)
    return stub


class GenerateInvoicePdfTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = CompanySettings.get_instance()
        cls.company.registro_comercial = 'A54877'
        cls.company.save(update_fields=['registro_comercial'])
        cls.user = User.objects.create_user(
            'pdf', 'pdf@example.com', 'pass', first_name='Cliente', last_name='PDF'
        )
        cls.customer = Customer.objects.create(
            client_type='juridica',
            user=cls.user,
            company_name='Empresa PDF',
            reeup='123.4.5678',
            nit='12345678901',
            account='9001000000000001',
            agency_bank='Banco PDF',
        )
        cls.invoice = Invoice.objects.create(
            customer=cls.customer,
            number='PDF-0001',
            amount=Decimal('100.00'),
        )
        cls.item = InvoiceItem.objects.create(
            invoice=cls.invoice,
            descripcion='Servicio de prueba',
            cantidad=1,
            unidad_medida='U',
            precio=Decimal('100.00'),
        )

    def _generar(self, invoice=None, customer=None, item=None):
        """Corre el generador con el motor parcheado y devuelve el HTMLArmado."""
        with renderizador_ok(), pdf_stub() as mock_html:
            mock_html.return_value.write_pdf.return_value = b'%PDF-1.4 stub'
            generate_invoice_pdf_standalone(
                invoice or self.invoice,
                customer or self.customer,
                [item or self.item],
            )
        return mock_html.call_args.kwargs['string']

    def test_el_html_se_genera_con_el_numero_de_la_factura(self):
        html = self._generar()

        # La ruta del template es lo que se rompió: si vuelve a cambiar de nombre,
        # esto falla con TemplateDoesNotExist en vez de un assert leible.
        self.assertIn(self.invoice.number, html)
        self.assertIn('Empresa PDF', html)
        self.assertIn('Servicio de prueba', html)

    def test_el_pdf_queda_adjunto_en_la_factura(self):
        self._generar()

        self.invoice.refresh_from_db()
        self.assertTrue(self.invoice.pdf)

    def test_sin_motor_falla_antes_de_tocar_la_factura(self):
        """El preflight va antes del render: sin la pila de Pango el error tiene que
        decir qué instalar, y la factura no debe quedar con un PDF a medio escribir."""
        with (
            patch(PREFLIGHT, side_effect=RuntimeError('faltan las librerías del sistema')),
            pdf_stub() as mock_html,
            self.assertRaises(RuntimeError),
        ):
            generate_invoice_pdf_standalone(self.invoice, self.customer, [self.item])

        mock_html.assert_not_called()
        self.invoice.refresh_from_db()
        self.assertFalse(self.invoice.pdf)


class BloqueProveedorTests(TestCase):
    """El bloque del ejecutor: registro comercial, número y fecha del contrato.

    Venían hardcodeados a `''` en el contexto, así que la factura salía con tres
    líneas en blanco aunque el contrato existiera.
    """

    @classmethod
    def setUpTestData(cls):
        cls.company = CompanySettings.get_instance()
        cls.company.registro_comercial = 'A54877'
        cls.company.save(update_fields=['registro_comercial'])
        cls.user = User.objects.create_user('prov', 'prov@example.com', 'pass')
        cls.customer = Customer.objects.create(
            client_type='juridica',
            user=cls.user,
            company_name='Empresa Proveedora',
            account='9001000000000003',
            address='Calle 1',
            phone='71234567',
        )
        cls.service = Service.objects.create(
            user=cls.user,
            title='Servicio',
            summary='Servicio',
            service_type=Service.COMMERCIAL,
            code='PROV-001',
            price=Decimal('100.00'),
        )
        cls.subscription = ServiceSubscription.objects.create(
            customer=cls.customer,
            service=cls.service,
            start_date=timezone.now(),
        )
        cls.contract = Contract.objects.create(
            subscription=cls.subscription,
            number='CONT-2026-001',
            date=date(2026, 2, 3),
            commercial_registry='RC-ESPECIFICO',
        )
        cls.invoice = Invoice.objects.create(
            customer=cls.customer,
            subscription=cls.subscription,
            number='PROV-0001',
            amount=Decimal('100.00'),
        )
        cls.item = InvoiceItem.objects.create(
            invoice=cls.invoice,
            subscription=cls.subscription,
            descripcion='Servicio de prueba',
            cantidad=1,
            unidad_medida='U',
            precio=Decimal('100.00'),
        )

    def _generar(self, invoice=None):
        with renderizador_ok(), pdf_stub() as mock_html:
            mock_html.return_value.write_pdf.return_value = b'%PDF-1.4 stub'
            generate_invoice_pdf_standalone(invoice or self.invoice, self.customer, [self.item])
        return mock_html.call_args.kwargs['string']

    def test_el_contrato_llena_registro_numero_y_fecha(self):
        html = self._generar()

        self.assertIn('RC-ESPECIFICO', html)
        self.assertIn('CONT-2026-001', html)
        # Formato dd/mm/yyyy, el mismo que usa el período de facturación.
        self.assertIn('03/02/2026', html)

    def test_el_registro_del_contrato_gana_al_de_la_empresa(self):
        """El del contrato es el más específico (es el de esa suscripción)."""
        self.assertNotEqual(self.contract.commercial_registry, self.company.registro_comercial)

        html = self._generar()

        self.assertIn('RC-ESPECIFICO', html)
        self.assertNotIn(self.company.registro_comercial, html)

    def test_sin_contrato_cae_al_registro_de_la_empresa(self):
        """Una factura sin suscripción (o con suscripción sin contrato) no rompe:
        `subscription.contract` es un OneToOne y lanzaría DoesNotExist."""
        manual = Invoice.objects.create(
            customer=self.customer,
            number='PROV-0002',
            amount=Decimal('100.00'),
        )

        html = self._generar(invoice=manual)

        self.assertIn(self.company.registro_comercial, html)
        self.assertNotIn('RC-ESPECIFICO', html)

    def test_registro_vacio_del_contrato_cae_al_de_la_empresa(self):
        self.contract.commercial_registry = ''
        self.contract.save(update_fields=['commercial_registry'])

        html = self._generar()

        self.assertIn(self.company.registro_comercial, html)

    def test_suscripcion_sin_contrato_no_rompe(self):
        self.contract.hard_delete()
        # Una factura propia, no la compartida: `invoice.subscription` y
        # `subscription.contract` son accesores que cachean en la instancia, y
        # la factura de `setUpTestData` ya se resolvió en los tests anteriores.
        huerfana = Invoice.objects.create(
            customer=self.customer,
            number='PROV-0003',
            amount=Decimal('100.00'),
        )

        html = self._generar(invoice=huerfana)

        self.assertIn(self.company.registro_comercial, html)
        self.assertNotIn('RC-ESPECIFICO', html)


class BloqueClienteTests(TestCase):
    """El bloque del cliente cambia según `client_type`.

    La plantilla imprime un bloque fijo de 7 líneas, así que una persona natural
    se quedaba con 4 líneas vacías (Reeup, NIT, cuenta y agencia) y sin nombre.
    """

    @classmethod
    def setUpTestData(cls):
        cls.company = CompanySettings.get_instance()
        cls.company.registro_comercial = 'A54877'
        cls.company.save(update_fields=['registro_comercial'])
        cls.service = Service.objects.create(
            user=User.objects.create_user('blocks', 'blocks@example.com', 'pass'),
            title='Servicio',
            summary='Servicio',
            service_type=Service.COMMERCIAL,
            code='BLOQ-001',
            price=Decimal('100.00'),
        )
        cls.juridica_user = User.objects.create_user(
            'juridica', 'juridica@example.com', 'pass', first_name='Empresa', last_name='Jurídica'
        )
        cls.juridica = Customer.objects.create(
            client_type='juridica',
            user=cls.juridica_user,
            company_name='Empresa Jurídica',
            reeup='123.4.5678',
            nit='12345678901',
            account='9001000000000004',
            agency_bank='Banco Jurídico',
            address='Calle Empresa 1',
            phone='71234567',
        )
        cls.natural_user = User.objects.create_user(
            'natural', 'natural@example.com', 'pass', first_name='Ana', last_name='Norte'
        )
        cls.natural = natural_customer(
            cls.natural_user,
            identity_document='34111234567',
            account='9001000000000005',
            address='Calle Persona 2',
            phone='71234568',
        )

    def _generar(self, customer, numero):
        subscription = ServiceSubscription.objects.create(
            customer=customer,
            service=self.service,
            start_date=timezone.now(),
        )
        Contract.objects.create(
            subscription=subscription,
            number='CONT-BLOQ-001',
            date=date(2026, 2, 3),
            commercial_registry='RC-BLOQ',
        )
        invoice = Invoice.objects.create(
            customer=customer,
            subscription=subscription,
            number=numero,
            amount=Decimal('100.00'),
        )
        item = InvoiceItem.objects.create(
            invoice=invoice,
            subscription=subscription,
            descripcion='Servicio de prueba',
            cantidad=1,
            unidad_medida='U',
            precio=Decimal('100.00'),
        )
        with renderizador_ok(), pdf_stub() as mock_html:
            mock_html.return_value.write_pdf.return_value = b'%PDF-1.4 stub'
            generate_invoice_pdf_standalone(invoice, customer, [item])
        return mock_html.call_args.kwargs['string']

    def test_juridica_imprime_los_campos_de_la_empresa(self):
        html = self._generar(self.juridica, 'BLOQ-JUR-0001')

        self.assertIn('Empresa Jurídica', html)
        self.assertIn('123.4.5678', html)
        self.assertIn('12345678901', html)
        self.assertIn('9001000000000004', html)
        self.assertIn('Banco Jurídico', html)
        # Una jurídica no tiene (ni debe imprimir) documento de identidad.
        self.assertNotIn('Documento de identidad', html)

    def test_natural_imprime_el_nombre_de_la_persona_y_su_documento(self):
        html = self._generar(self.natural, 'BLOQ-NAT-0001')

        self.assertIn('Ana Norte', html)
        self.assertIn('34111234567', html)
        self.assertIn('Documento de identidad', html)

    def test_natural_no_imprime_los_campos_de_la_empresa(self):
        html = self._generar(self.natural, 'BLOQ-NAT-0002')

        # Los valores existen en el modelo, pero el bloque no los imprime: por eso
        # el HTML no puede contenerlos ni siquiera de coincidir con otra cosa.
        self.assertEqual(self.natural.reeup, None)
        self.assertEqual(self.natural.nit, None)
        self.assertNotIn('9001000000000005', html)

    def test_ambos_llevan_el_bloque_del_ejecutor_completo(self):
        for customer, numero in (
            (self.juridica, 'BLOQ-JUR-0003'),
            (self.natural, 'BLOQ-NAT-0003'),
        ):
            html = self._generar(customer, numero)
            self.assertIn('CONT-BLOQ-001', html)
            self.assertIn('03/02/2026', html)
            self.assertIn('RC-BLOQ', html)

    def test_la_juridica_imprime_la_razon_social_aunque_la_cuenta_tenga_nombre(self):
        """La cuenta de un cliente jurídico puede tener nombre propio (el de quien
        la gestiona), pero la factura lleva la razón social: es lo que se
        imprimía antes y es lo que identifica al ente en el documento."""
        self.juridica_user.first_name = 'Ana'
        self.juridica_user.last_name = 'Norte'
        self.juridica_user.save(update_fields=['first_name', 'last_name'])
        juridica = Customer.objects.get(pk=self.juridica.pk)

        html = self._generar(juridica, 'BLOQ-JUR-0004')

        self.assertIn('Empresa Jurídica', html)
        self.assertNotIn('Ana Norte', html)

    def test_natural_sin_nombre_cae_a_razon_social_y_luego_a_username(self):
        """La degradación es por tipo: natural -> persona -> razón social ->
        username, sin imprimir nunca la línea en blanco."""
        customer = natural_customer(
            User.objects.create_user('solo_razon', 'razon@example.com', 'pass'),
            company_name='Razón Social Residual',
            identity_document='34111888888',
            account='9001000000000007',
            address='Calle Razon 4',
            phone='71234570',
        )

        html = self._generar(customer, 'BLOQ-NAT-0004')

        self.assertIn('Razón Social Residual', html)
        self.assertNotIn('solo_razon', html)

    def test_sin_nombre_ninguno_cae_al_username(self):
        """Nunca se imprime una línea de nombre en blanco."""
        anonimo = User.objects.create_user('sin_nombre', 'anonimo@example.com', 'pass')
        customer = natural_customer(
            anonimo,
            identity_document='34111999999',
            account='9001000000000006',
            address='Calle Anonimo 3',
            phone='71234569',
        )

        html = self._generar(customer, 'BLOQ-ANON-0001')

        self.assertIn('sin_nombre', html)
