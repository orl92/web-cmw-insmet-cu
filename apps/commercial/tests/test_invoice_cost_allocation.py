"""El reparto por centro de costo de la factura tiene que ser real, no un literal.

Contexto: se compararon tres facturas reales del CMP (182, 279, 276) contra el
PDF que genera el sistema. El template traía el texto fijo
`Centro de Costo 700.50107 100 %`, y las facturas reales reparten el importe de
una forma que ese literal no puede representar:

    182: 700.50107 100%
    279: 700.50207 90% + 700.50407 10%
    276: 700.50107 25% + 700.50207 65% + 700.50407 10%

Con el literal fijo, dos de las tres facturas reales salían con la imputación
contable equivocada, y eso en un documento con valor legal no es cosmético.

Dos hechos deliberadamente fijados acá, porque son la razón de diseño de todo
el modelo:

1. El reparto NO es derivable de los ítems. La factura 276 tiene un único ítem
   (cant 4, $1 281.40) repartido en tres centros 25/65/10: con una sola línea es
   imposible obtener tres porcentajes desde los montos. El reparto es una
   decisión del operador, guardada como dato.
2. El centro por defecto SÍ es derivable, porque viaja embebido en el prefijo
   del código de servicio (`700501072507005` -> `700.50107`). Eso permite
   prellenar, no deducir.

Por eso `InvoiceCostAllocation` existe como dato, y el prefill se marca
explícitamente como punto de partida.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.commercial.forms.invoice import InvoiceCostAllocationFormSet
from apps.commercial.models import (
    Customer,
    Invoice,
    InvoiceCostAllocation,
    InvoiceItem,
    Service,
    ServiceSubscription,
)
from apps.commercial.views.invoice_utils import (
    _prefill_cost_allocations_from_items,
    generate_invoice_pdf_standalone,
)
from apps.core.models import CompanySettings, SiteConfiguration
from config.huey import huey

HTML = 'apps.commercial.views.invoice_utils.HTML'
PREFLIGHT = 'apps.commercial.views.invoice_utils.require_pdf_renderer'


class _InvoiceFactoryMixin:
    """Cliente + factura + ítems, con los prerrequisitos reales del negocio.

    Se exige `codigo` en los ítems porque de ahí se deriva el centro de costo;
    un ítem sin código no aporta centro y el prefill lo descarta, que es
    intencional (no se inventa un centro) y por eso tiene su propio test.
    """

    @classmethod
    def _crear_factura(cls, codigos=('700501072507005',), importe='35744.78'):
        company = CompanySettings.get_instance()
        company.registro_comercial = 'A54877'
        company.save(update_fields=['registro_comercial'])
        user = User.objects.create_user(
            'costo', 'costo@example.com', 'pass', first_name='Cli', last_name='Costo'
        )
        customer = Customer.objects.create(
            client_type='juridica',
            user=user,
            company_name='Empresa Costos',
            reeup='123.4.5678',
            nit='12345678901',
            account='9001000000000001',
            agency_bank='Banco Costos',
        )
        invoice = Invoice.objects.create(
            customer=customer, number=f'CC-{len(codigos)}', amount=Decimal(importe)
        )
        items = [
            InvoiceItem.objects.create(
                invoice=invoice,
                codigo=codigo,
                descripcion=f'Servicio {codigo}',
                cantidad=1,
                unidad_medida='U',
                precio=Decimal(importe) / len(codigos),
            )
            for codigo in codigos
        ]
        return invoice, customer, items


class InvoiceCostAllocationModelTests(_InvoiceFactoryMixin, TestCase):
    def test_guarda_la_asignacion_con_su_porcentaje(self):
        invoice, _customer, _items = self._crear_factura()

        asignacion = InvoiceCostAllocation.objects.create(
            invoice=invoice, codigo='700.50107', porcentaje=Decimal('25.00')
        )

        asignacion.refresh_from_db()
        self.assertEqual(asignacion.codigo, '700.50107')
        self.assertEqual(asignacion.porcentaje, Decimal('25.00'))

    def test_los_cuatro_permisos_personalizados_existen(self):
        for permisos in InvoiceCostAllocation._meta.permissions:
            self.assertIn(permisos[1], {'Ver', 'Añadir', 'Editar', 'Eliminar'})

    def test_no_hay_permisos_por_defecto(self):
        self.assertEqual(InvoiceCostAllocation._meta.default_permissions, ())

    def test_clean_rechaza_porcentaje_cero(self):
        invoice, _customer, _items = self._crear_factura()

        with self.assertRaises(ValidationError):
            InvoiceCostAllocation(
                invoice=invoice, codigo='700.50107', porcentaje=Decimal('0')
            ).clean()

    def test_clean_rechaza_porcentaje_negativo(self):
        invoice, _customer, _items = self._crear_factura()

        with self.assertRaises(ValidationError):
            InvoiceCostAllocation(
                invoice=invoice, codigo='700.50107', porcentaje=Decimal('-10')
            ).clean()

    def test_el_borrado_logico_conserva_la_imputacion(self):
        """`Invoice` es `SoftDeleteModel`: anular no debe perder la trazabilidad.

        Si la imputación desapareciera al anular, la factura anulada dejaría de
        explicar a qué centros se imputó, que es justo lo que hace falta para
        auditar. Sólo el borrado físico se lleva las filas.
        """
        invoice, _customer, _items = self._crear_factura()
        InvoiceCostAllocation.objects.create(
            invoice=invoice, codigo='700.50107', porcentaje=Decimal('100.00')
        )

        invoice.delete()

        self.assertEqual(InvoiceCostAllocation.objects.count(), 1)

    def test_la_asignacion_muere_con_el_borrado_fisico(self):
        invoice, _customer, _items = self._crear_factura()
        InvoiceCostAllocation.objects.create(
            invoice=invoice, codigo='700.50107', porcentaje=Decimal('100.00')
        )

        invoice.hard_delete()

        self.assertEqual(InvoiceCostAllocation.objects.count(), 0)


class PrefillCostAllocationsTests(TestCase):
    """El centro sale del prefijo del código; el reparto es un punto de partida."""

    def _item(self, codigo):
        return InvoiceItem(codigo=codigo)

    def test_un_solo_centro_recibe_el_ciento_por_ciento(self):
        items = [self._item('700501072507005'), self._item('700501072507008')]

        resultado = _prefill_cost_allocations_from_items(items)

        self.assertEqual(resultado, [{'codigo': '700.50107', 'porcentaje': Decimal('100.00')}])

    def test_dos_centros_se_reparten_a_la_mitad(self):
        items = [self._item('700501072507005'), self._item('700502072507017')]

        resultado = _prefill_cost_allocations_from_items(items)

        self.assertEqual(
            resultado,
            [
                {'codigo': '700.50107', 'porcentaje': Decimal('50.00')},
                {'codigo': '700.50207', 'porcentaje': Decimal('50.00')},
            ],
        )

    def test_tres_centros_suman_exactamente_el_ciento(self):
        """El residuo va al último: 100/3 no es exacto y un reparto que no suma
        100 es exactamente el defecto que este modelo viene a arreglar."""
        items = [
            self._item('700501072507005'),
            self._item('700502072507017'),
            self._item('700504072507021'),
        ]

        resultado = _prefill_cost_allocations_from_items(items)

        self.assertEqual(len(resultado), 3)
        self.assertEqual(sum(a['porcentaje'] for a in resultado), Decimal('100.00'))
        # El residuo del redondeo va a la última fila: las tres valen 33.33 y
        # 100 - 66.66 = 33.34, que es lo que cierra la suma en 100.00 exactos.
        self.assertEqual(
            [a['porcentaje'] for a in resultado],
            [Decimal('33.33'), Decimal('33.33'), Decimal('33.34')],
        )

    def test_centros_repetidos_se_agrupan_en_una_fila(self):
        items = [self._item('700501072507005'), self._item('700501072507008')]

        resultado = _prefill_cost_allocations_from_items(items)

        self.assertEqual(len(resultado), 1)

    def test_un_codigo_corto_se_descarta_en_vez_de_inventar_un_centro(self):
        resultado = _prefill_cost_allocations_from_items([self._item('123')])

        self.assertEqual(resultado, [])

    def test_sin_items_no_hay_prefill(self):
        self.assertEqual(_prefill_cost_allocations_from_items([]), [])


class InvoiceCostAllocationFormSetTests(TestCase):
    """La suma 100 % se valida en el formset, no en el modelo.

    En el modelo impediría borrar una fila con `can_delete` y reescribir el
    reparto, que es la operación normal del operador.
    """

    def _formset(self, filas):
        return InvoiceCostAllocationFormSet(
            data={
                'form-TOTAL_FORMS': str(len(filas)),
                'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0',
                'form-MAX_NUM_FORMS': '1000',
                **{
                    clave: valor
                    for indice, fila in enumerate(filas)
                    for clave, valor in (
                        (f'form-{indice}-codigo', fila['codigo']),
                        (f'form-{indice}-porcentaje', fila['porcentaje']),
                        (f'form-{indice}-DELETE', fila.get('DELETE', '')),
                    )
                },
            },
            prefix='form',
        )

    def test_acepta_un_reparto_que_suma_cien(self):
        formset = self._formset(
            [
                {'codigo': '700.50107', 'porcentaje': '90.00'},
                {'codigo': '700.50407', 'porcentaje': '10.00'},
            ]
        )

        self.assertTrue(formset.is_valid(), formset.errors)

    def test_rechaza_un_reparto_que_no_suma_cien(self):
        formset = self._formset([{'codigo': '700.50107', 'porcentaje': '90.00'}])

        self.assertFalse(formset.is_valid())
        self.assertIn('100', str(formset.non_form_errors()))

    def test_rechaza_un_reparto_que_pasa_el_cien(self):
        formset = self._formset(
            [
                {'codigo': '700.50107', 'porcentaje': '60.00'},
                {'codigo': '700.50407', 'porcentaje': '60.00'},
            ]
        )

        self.assertFalse(formset.is_valid())

    def test_una_fila_borrada_se_excluye_de_la_suma(self):
        """`can_delete` tiene que recalcular sobre las filas vivas: si no, no se
        podría corregir un repartoEquivocado."""
        formset = self._formset(
            [
                {'codigo': '700.50107', 'porcentaje': '100.00'},
                {'codigo': '700.50407', 'porcentaje': '10.00', 'DELETE': 'on'},
            ]
        )

        self.assertTrue(formset.is_valid(), formset.non_form_errors())

    def test_todas_borradas_no_suman_cien(self):
        """Sin filas vivas no hay reparto, y una factura comercial sin imputación
        es justo el defecto que este formset viene a impedir."""
        formset = self._formset([{'codigo': '700.50107', 'porcentaje': '100.00', 'DELETE': 'on'}])

        self.assertFalse(formset.is_valid())


class InvoiceCostAllocationPdfTests(_InvoiceFactoryMixin, TestCase):
    """El PDF imprime lo guardado, no el literal que estaba en el template."""

    def _render(self, invoice, customer, items):
        with patch(PREFLIGHT, return_value=None), patch(HTML, autospec=True) as mock_html:
            mock_html.return_value.write_pdf.return_value = b'%PDF-1.4 stub'
            generate_invoice_pdf_standalone(
                invoice, customer, date(2026, 1, 1), date(2026, 1, 31), items
            )
        return mock_html.call_args.kwargs['string']

    def test_imprime_una_linea_por_centro_de_costo(self):
        invoice, customer, items = self._crear_factura()
        InvoiceCostAllocation.objects.create(
            invoice=invoice, codigo='700.50107', porcentaje=Decimal('25.00')
        )
        InvoiceCostAllocation.objects.create(
            invoice=invoice, codigo='700.50207', porcentaje=Decimal('65.00')
        )
        InvoiceCostAllocation.objects.create(
            invoice=invoice, codigo='700.50407', porcentaje=Decimal('10.00')
        )

        html = self._render(invoice, customer, items)

        self.assertIn('Centro de Costo 700.50107 25 %', html)
        self.assertIn('Centro de Costo 700.50207 65 %', html)
        self.assertIn('Centro de Costo 700.50407 10 %', html)

    def test_una_factura_sin_asignaciones_no_imprime_el_centro_hardcodeado(self):
        """Regresión del defecto original: el template traía el literal fijo."""
        invoice, customer, items = self._crear_factura()

        html = self._render(invoice, customer, items)

        self.assertNotIn('700.50107', html)
        self.assertNotIn('Centro de Costo', html)

    def test_el_total_sigue_presente(self):
        invoice, customer, items = self._crear_factura()
        InvoiceCostAllocation.objects.create(
            invoice=invoice, codigo='700.50107', porcentaje=Decimal('100.00')
        )

        html = self._render(invoice, customer, items)

        self.assertIn('TOTAL', html)
        self.assertIn('35744.78', html)


class InvoiceCostAllocationVistaTests(TestCase):
    """De extremo a extremo: lo que manda el operador queda en la factura.

    Los tests de arriba prueban modelo, formset, prefill y render por separado.
    Falta el cableado: que el POST guarde de verdad las filas, y que un reparto
    inválido no deje una factura a medias en la base.
    """

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        company = CompanySettings.get_instance()
        company.registro_comercial = 'A54877'
        company.save(update_fields=['registro_comercial'])
        # `CheckUserProfileMiddleware` rebota a actualizar el perfil a quien no
        # tiene nombre y apellido, así que un superuser sin ellos nunca llega
        # a la vista.
        cls.admin = User.objects.create_superuser(
            username='costadmin',
            email='cost@example.com',
            password='pass',  # pragma: allowlist secret
            first_name='Admin',
            last_name='Super',
        )
        cls.customer = Customer.objects.create(
            client_type='juridica',
            user=User.objects.create_user(
                'costocust',
                'costocust@example.com',
                'pass',
                first_name='Cli',
                last_name='Costo',
            ),
            company_name='Empresa Costos',
            reeup='123.4.5678',
            nit='12345678901',
            account='9001000000000001',
            agency_bank='Banco Costos',
        )
        cls.service = Service.objects.create(
            user=cls.admin,
            title='Pronóstico diario',
            summary='Pronóstico puntual para RPC',
            service_type='commercial',
            service_category='pronostico',
            # El prefijo 700.50107 es el centro de costo que se precarga.
            code='700501072507005',
            price=Decimal('45.00'),
        )
        cls.subscription = ServiceSubscription.objects.create(
            customer=cls.customer,
            service=cls.service,
            quantity=10,
            payment_status='pending',
            start_date=timezone.now(),
        )
        cls.url = reverse('commercial:factura_create')

    def setUp(self):
        # El POST encola la tarea real de PDF; la cola se vacía por corrida, no
        # por test, así que hay que limpiarla en los dos sentidos.
        huey.flush()
        self.addCleanup(huey.flush)
        self.client.force_login(self.admin)

    def _formulario(self, **cost):
        datos = {
            'customer': self.customer.pk,
            'start_date': date(2026, 1, 1).isoformat(),
            'end_date': date(2026, 1, 31).isoformat(),
            'commercial_registry': 'REG-COST',
            'subscriptions': [str(self.subscription.pk)],
            'cost_allocations-TOTAL_FORMS': '1',
            'cost_allocations-INITIAL_FORMS': '0',
            'cost_allocations-MIN_NUM_FORMS': '0',
            'cost_allocations-MAX_NUM_FORMS': '1000',
        }
        datos.update(cost)
        return datos

    def _factura_creada(self):
        invoice = Invoice.objects.filter(customer=self.customer).order_by('-id').first()
        self.assertIsNotNone(invoice, 'no se creó ninguna factura para el cliente')
        return invoice

    def test_el_reparto_del_operador_queda_guardado(self):
        self.client.post(
            self.url,
            self._formulario(
                **{
                    'cost_allocations-0-codigo': '700.50107',
                    'cost_allocations-0-porcentaje': '100.00',
                }
            ),
        )

        invoice = self._factura_creada()
        self.assertEqual(
            [(a.codigo, a.porcentaje) for a in invoice.cost_allocations.all()],
            [('700.50107', Decimal('100.00'))],
        )

    def test_un_reparto_de_varios_centros_queda_guardado_completo(self):
        """El caso 276 real: tres centros en una sola factura."""
        self.client.post(
            self.url,
            self._formulario(
                **{
                    'cost_allocations-TOTAL_FORMS': '3',
                    'cost_allocations-0-codigo': '700.50107',
                    'cost_allocations-0-porcentaje': '25.00',
                    'cost_allocations-1-codigo': '700.50207',
                    'cost_allocations-1-porcentaje': '65.00',
                    'cost_allocations-2-codigo': '700.50407',
                    'cost_allocations-2-porcentaje': '10.00',
                }
            ),
        )

        invoice = self._factura_creada()
        self.assertEqual(
            [(a.codigo, a.porcentaje) for a in invoice.cost_allocations.all()],
            [
                ('700.50107', Decimal('25.00')),
                ('700.50207', Decimal('65.00')),
                ('700.50407', Decimal('10.00')),
            ],
        )

    def test_un_reparto_que_no_suma_cien_no_crea_la_factura(self):
        """El error vuelve al formulario y no deja una factura a medias."""
        self.client.post(
            self.url,
            self._formulario(
                **{
                    'cost_allocations-0-codigo': '700.50107',
                    'cost_allocations-0-porcentaje': '90.00',
                }
            ),
        )

        self.assertFalse(Invoice.objects.filter(customer=self.customer).exists())

    def test_el_formulario_abre_con_el_centro_precargado(self):
        """Al regenerar, el centro del servicio viene solo: el operador confirma."""
        response = self.client.get(self.url, {'regenerar': str(self.subscription.uuid)})

        formset = response.context['cost_allocations_formset']
        self.assertEqual([f.initial.get('codigo') for f in formset.forms], ['700.50107'])
