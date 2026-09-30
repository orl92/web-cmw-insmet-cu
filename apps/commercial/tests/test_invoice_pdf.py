"""El PDF de la factura tiene que poder generarse.

`generate_invoice_pdf_standalone` renderiza un template por ruta y después llama a
wkhtmltopdf. La ruta quedó apuntando a `factura_template.html` cuando la
restructuración de templates (1043f55) renombró el archivo a `template.html`: el
resultado era `TemplateDoesNotExist` SIEMPRE, sin importar el binario. Con eso,
la tarea del worker moría antes de enviar el correo y el fallback "Ver PDF" del
listado absorbía la excepción y dejaba el PDF vacío.

Se testea con `pdfkit.from_string` parcheado: lo que se quiere fijar acá es que el
HTML se arma (o sea, que la ruta del template existe y el contexto le sirve), no
la calidad del PDF.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from apps.commercial.models import Customer, Invoice, InvoiceItem
from apps.commercial.views.invoice_utils import generate_invoice_pdf_standalone

# El parche va donde se usa (el modulo bajo prueba), no donde se llama.
WHICH = 'apps.commercial.views.invoice_utils.shutil.which'
PDFKIT = 'apps.commercial.views.invoice_utils.pdfkit.from_string'
BINARIO = '/usr/bin/wkhtmltopdf'


def con_binario():
    """El preflight se pasa por alto: simula que wkhtmltopdf esta instalado."""
    return patch(WHICH, return_value=BINARIO)


def pdf_stub():
    """Captura el HTML que se le pasa a wkhtmltopdf y devuelve bytes de PDF."""
    return patch(PDFKIT, return_value=b'%PDF-1.4 stub')


class GenerateInvoicePdfTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('pdf', 'pdf@example.com', 'pass')
        cls.customer = Customer.objects.create(
            client_type='juridica',
            user=cls.user,
            company_name='Empresa PDF',
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

    def test_el_html_se_genera_con_el_numero_de_la_factura(self):
        with con_binario(), pdf_stub() as mock_pdfkit:
            generate_invoice_pdf_standalone(
                self.invoice,
                self.customer,
                date(2026, 1, 1),
                date(2026, 1, 31),
                '',
                [self.item],
            )

        html = mock_pdfkit.call_args[0][0]
        # La ruta del template es lo que se rompió: si vuelve a cambiar de nombre,
        # esto falla con TemplateDoesNotExist en vez de un assert leible.
        self.assertIn(self.invoice.number, html)
        self.assertIn('Empresa PDF', html)
        self.assertIn('Servicio de prueba', html)

    def test_el_pdf_queda_adjunto_en_la_factura(self):
        with con_binario(), pdf_stub():
            generate_invoice_pdf_standalone(
                self.invoice,
                self.customer,
                date(2026, 1, 1),
                date(2026, 1, 31),
                '',
                [self.item],
            )

        self.invoice.refresh_from_db()
        self.assertTrue(self.invoice.pdf)

    def test_sin_binario_falla_antes_de_tocar_la_factura(self):
        """El preflight va antes del render: sin `wkhtmltopdf` el error tiene que
        decir qué instalar, y la factura no debe quedar con un PDF a medio escribir."""
        with (
            patch(WHICH, return_value=None),
            pdf_stub() as mock_pdfkit,
            self.assertRaises(RuntimeError),
        ):
            generate_invoice_pdf_standalone(
                self.invoice,
                self.customer,
                date(2026, 1, 1),
                date(2026, 1, 31),
                '',
                [self.item],
            )

        mock_pdfkit.assert_not_called()
        self.invoice.refresh_from_db()
        self.assertFalse(self.invoice.pdf)
