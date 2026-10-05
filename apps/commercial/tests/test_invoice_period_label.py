"""El período facturado es texto libre, no un rango de fechas.

Contexto: al comparar el PDF que genera el sistema contra las tres facturas
reales del CMP (182, 279, 276), el template componía el período a partir de dos
fechas:

    periodo = f'Desde {start_date} hasta {end_date}'

y el único camino de respaldo pasaba la misma fecha dos veces:

    start_date = invoice.issue_date
    end_date = invoice.issue_date

O sea, "Desde 15/06/2025 hasta 15/06/2025": un rango imposible que ninguna
factura real usa. Las reales escriben el período a mano, como texto:

    182: "Mes de mayo y junio de 2025"
    279: "octubre y noviembre del 2025"
    276: "Mes de diciembre de 2025"

Ninguno de esos tres textos se puede derivar de dos campos de fecha: "mayo y
junio" no tiene fecha de inicio, "octubre y noviembre del 2025" tampoco. Por eso
el período es un `CharField` y no dos `DateField`.

El respaldo no es una migración de datos. En este proyecto las migraciones están
gitignored y CI regenera con `makemigrations`, así que una migración de datos se
perdería en silencio; el respaldo en tiempo de lectura cubre a las facturas
viejas sin depender del historial de migraciones.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from apps.commercial.forms.invoice import InvoiceForm
from apps.commercial.models import Customer, Invoice, InvoiceItem
from apps.commercial.views.invoice_utils import generate_invoice_pdf_standalone
from apps.core.models import CompanySettings

HTML = 'apps.commercial.views.invoice_utils.HTML'
PREFLIGHT = 'apps.commercial.views.invoice_utils.require_pdf_renderer'


class _FakeHTML:
    """WeasyPrint stand-in: acá lo que importa es el HTML que arma el contexto."""

    ultima = None

    def __init__(self, string=None, **kwargs):
        self.string = string
        _FakeHTML.ultima = self

    def write_pdf(self, *args, **kwargs):
        return b'%PDF-1.4 test'


class PeriodLabelTests(TestCase):
    def setUp(self):
        company = CompanySettings.get_instance()
        company.registro_comercial = 'A54877'
        company.save(update_fields=['registro_comercial'])
        self.customer = Customer.objects.create(
            client_type='juridica',
            user=User.objects.create_user(
                'periodo',
                'periodo@example.com',
                'pass',  # pragma: allowlist secret
                first_name='Ana',
                last_name='Norte',
            ),
            company_name='Empresa Periodo',
            reeup='123.4.5678',
            nit='12345678901',
            account='9001000000000001',
            agency_bank='Banco Periodo',
        )

    def _factura(self, period_label=''):
        invoice = Invoice.objects.create(
            customer=self.customer,
            number=f'PL-{period_label[:6] or "vacia"}',
            amount=Decimal('100.00'),
        )
        if period_label:
            invoice.period_label = period_label
            invoice.save(update_fields=['period_label'])
        InvoiceItem.objects.create(
            invoice=invoice,
            codigo='700501072507005',
            descripcion='Servicio de prueba',
            cantidad=1,
            unidad_medida='U',
            precio=Decimal('100.00'),
        )
        return invoice

    def _html(self, invoice):
        """Renderiza sin WeasyPrint y devuelve el HTML que se le iba a pasar."""
        _FakeHTML.ultima = None
        with patch(PREFLIGHT), patch(HTML, _FakeHTML):
            generate_invoice_pdf_standalone(invoice, self.customer, invoice.items.all())
        return _FakeHTML.ultima.string

    def _rango_imposible(self, invoice):
        """El texto exacto que producía el defecto original."""
        f = invoice.issue_date.strftime('%d/%m/%Y')
        return f'Desde {f} hasta {f}'

    # ------------------------------------------------------------------ modelo

    def test_el_periodo_viene_vaio_por_defecto(self):
        """`blank=True` es lo que hace opcional el campo en el formulario."""
        self.assertTrue(Invoice._meta.get_field('period_label').blank)

    def test_el_periodo_acepta_texto_libre(self):
        invoice = self._factura('Mes de mayo y junio de 2025')

        invoice.refresh_from_db()

        self.assertEqual(invoice.period_label, 'Mes de mayo y junio de 2025')

    def test_un_periodo_no_se_trunca_en_la_base_de_datos(self):
        """El texto completo es lo que va al PDF, sin recortes silenciosos."""
        invoice = self._factura('Mes de mayo y junio de 2025')

        invoice.refresh_from_db()

        self.assertEqual(invoice.period_label, 'Mes de mayo y junio de 2025')

    # --------------------------------------------------------------------- PDF

    def test_el_pdf_imprime_el_periodo_tal_como_se_escribio(self):
        invoice = self._factura('Mes de mayo y junio de 2025')

        self.assertIn('Mes de mayo y junio de 2025', self._html(invoice))

    def test_el_pdf_nunca_compone_un_rango_de_fechas(self):
        """Regresión del defecto original: "Desde X hasta X" con X == Y."""
        invoice = self._factura('Mes de diciembre de 2025')

        self.assertNotIn(self._rango_imposible(invoice), self._html(invoice))

    def test_sin_periodo_cae_a_la_fecha_de_emision(self):
        """Las facturas viejas no tienen el campo: no se rompen ni inventan rango."""
        invoice = self._factura()

        html = self._html(invoice)

        self.assertIn(invoice.issue_date.strftime('%d/%m/%Y'), html)
        self.assertNotIn(self._rango_imposible(invoice), html)

    # ---------------------------------------------------------------- formulario

    def _data_formulario(self, **extra):
        return {
            'customer': self.customer.pk,
            'start_date': date(2026, 1, 1).isoformat(),
            'end_date': date(2026, 1, 31).isoformat(),
            'commercial_registry': 'REG-PL',
            **extra,
        }

    def test_el_formulario_acepta_el_periodo(self):
        form = InvoiceForm(data=self._data_formulario(period_label='Mes de mayo y junio de 2025'))

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['period_label'], 'Mes de mayo y junio de 2025')

    def test_el_periodo_no_es_obligatorio_en_el_formulario(self):
        """Una factura vieja se sigue able to emitir sin escribir el período."""
        form = InvoiceForm(data=self._data_formulario())

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data.get('period_label', ''), '')
