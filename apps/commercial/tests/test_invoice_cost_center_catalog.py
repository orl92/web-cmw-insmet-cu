"""El campo «Centro de Costo» ofrece un catálogo, pero no restringe.

El problema: en la pantalla de creación de factura el centro de costo era un
`<input type="text">` libre. El operador tenía que recordar de memoria los
códigos (`700.50107`, `700.50207`), que hoy sólo se descubren escondidos en el
prefijo del código de servicio (`700501072507005` -> `700.50107`).

La solución es un `<datalist>` con los centros conocidos. Es un `<datalist>` y no
un `<select>` a propósito: reconoce en vez de recordar, y **no cierra la puerta**
a un centro nuevo. Las facturas reales 276 (25/65/10) y 279 (90/10) reparten a
centros que no salen de ningún código de servicio, así que un catálogo cerrado las
haría imposibles de cargar.

El reparto por porcentaje sigue siendo manual y la regla de sumar 100 % no se
toca: lo único que cambia es cómo se entra el centro.
"""

import re
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.commercial.models import (
    Contract,
    Customer,
    Invoice,
    InvoiceCostAllocation,
    Service,
)
from apps.commercial.tests.factories import next_nit, next_reeup
from apps.commercial.views.invoice_utils import centros_de_costo_conocidos
from apps.core.models import CompanySettings, SiteConfiguration
from config.huey import huey


class CentrosDeCostoConocidosTests(TestCase):
    """La unión de los centros de los servicios y de las imputaciones guardadas.

    El catálogo es una unión, no una lista cerrada: lo derivable de un código de
    servicio más lo que ya se imputó alguna vez. Un centro que no sale de ningún
    código (los de las facturas reales 276/279) no está en el catálogo hasta que
    alguien lo escribe, y cuando lo escribe pasa a estarlo.
    """

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        admin = User.objects.create_superuser(
            username='catalogoadmin',
            email='catalogo@example.com',
            password='pass',  # pragma: allowlist secret
            first_name='Admin',
            last_name='Catálogo',
        )
        customer = Customer.objects.create(
            client_type='juridica',
            user=User.objects.create_user(
                'catalogocust',
                'catalogocust@example.com',
                'pass',  # pragma: allowlist secret
                first_name='Cli',
                last_name='Catálogo',
            ),
            company_name='Empresa Catálogo S.A.',
            reeup='123.4.5678',
            nit='12345678901',
            account='9001000000000001',
            agency_bank='Banco Catálogo',
        )
        cls.factura = Invoice.objects.create(
            customer=customer, number='CAT-0001', amount=Decimal('100.00')
        )
        Service.objects.create(
            user=admin,
            title='Radar',
            summary='Monitoreo con radar',
            service_type=Service.COMMERCIAL,
            service_category='pronostico',
            code='700501072507005',  # centro 700.50107
            price=Decimal('45.00'),
        )
        Service.objects.create(
            user=admin,
            title='Apicultura',
            summary='Pronóstico apícola',
            service_type=Service.COMMERCIAL,
            service_category='agrometeo',
            code='700502072507017',  # centro 700.50207
            price=Decimal('80.00'),
        )

    def test_el_catalogo_es_la_union_ordenada_y_sin_duplicados(self):
        InvoiceCostAllocation.objects.create(
            invoice=self.factura, codigo='700.50207', porcentaje=Decimal('100.00')
        )

        self.assertEqual(centros_de_costo_conocidos(), ['700.50107', '700.50207'])

    def test_un_centro_ya_imputado_que_no_sale_de_ningun_servicio_entra_al_catalogo(self):
        """El centro `700.50407` de las facturas reales 276/279 no tiene servicio."""
        InvoiceCostAllocation.objects.create(
            invoice=self.factura, codigo='700.50407', porcentaje=Decimal('100.00')
        )

        self.assertEqual(
            centros_de_costo_conocidos(),
            ['700.50107', '700.50207', '700.50407'],
        )

    def test_los_centros_repetidos_aparecen_una_sola_vez(self):
        """Dos servicios que comparten prefijo, más una imputación del mismo centro."""
        Service.objects.create(
            user=User.objects.get(username='catalogoadmin'),
            title='Tormentas',
            summary='Tormentas eléctricas',
            service_type=Service.COMMERCIAL,
            service_category='pronostico',
            code='700501072507099',  # mismo centro 700.50107
            price=Decimal('10.00'),
        )
        InvoiceCostAllocation.objects.create(
            invoice=self.factura, codigo='700.50107', porcentaje=Decimal('100.00')
        )

        catalogo = centros_de_costo_conocidos()

        self.assertEqual(catalogo, ['700.50107', '700.50207'])
        self.assertEqual(len(catalogo), len(set(catalogo)))

    def test_un_codigo_de_servicio_corto_no_agrega_nada(self):
        """Un código de menos de 8 dígitos no contiene centro: no se inventa."""
        Service.objects.create(
            user=User.objects.get(username='catalogoadmin'),
            title='Corto',
            summary='Código sin centro',
            service_type=Service.COMMERCIAL,
            service_category='pronostico',
            code='123',
            price=Decimal('10.00'),
        )

        self.assertEqual(centros_de_costo_conocidos(), ['700.50107', '700.50207'])

    def test_un_codigo_de_servicio_no_numerico_no_agrega_nada(self):
        Service.objects.create(
            user=User.objects.get(username='catalogoadmin'),
            title='Texto',
            summary='Código no numérico',
            service_type=Service.COMMERCIAL,
            service_category='pronostico',
            code='ABC-DEF-123',
            price=Decimal('10.00'),
        )

        self.assertEqual(centros_de_costo_conocidos(), ['700.50107', '700.50207'])

    def test_un_servicio_no_comercial_no_aporta_centro(self):
        """Sólo los servicios comerciales entran: un código de otro tipo no es una imputación."""
        Service.objects.create(
            user=User.objects.get(username='catalogoadmin'),
            title='Público',
            summary='Servicio público',
            service_type='public',
            service_category='pronostico',
            code='700503072507031',  # sería el centro 700.50307
            price=Decimal('10.00'),
        )

        self.assertEqual(centros_de_costo_conocidos(), ['700.50107', '700.50207'])

    def test_sin_servicios_ni_imputaciones_el_catalogo_es_vacio(self):
        InvoiceCostAllocation.objects.all().delete()
        Service.objects.all().delete()

        self.assertEqual(centros_de_costo_conocidos(), [])


class CentrosDeCostoEnLaPantallaTests(TestCase):
    """El `<datalist>` se ofrece en la pantalla de creación y sobrevive al JS."""

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        company = CompanySettings.get_instance()
        company.registro_comercial = 'A54877'
        company.save(update_fields=['registro_comercial'])
        cls.admin = User.objects.create_superuser(
            username='catalogoview',
            email='catalogoview@example.com',
            password='pass',  # pragma: allowlist secret
            first_name='Admin',
            last_name='Catálogo',
        )
        Service.objects.create(
            user=cls.admin,
            title='Radar',
            summary='Monitoreo con radar',
            service_type=Service.COMMERCIAL,
            service_category='pronostico',
            code='700501072507005',  # centro 700.50107
            price=Decimal('45.00'),
        )
        cls.url = reverse('commercial:factura_create')

    def setUp(self):
        self.client.force_login(self.admin)

    def _html(self):
        return self.client.get(self.url).content.decode()

    def test_la_pantalla_renderiza_el_datalist_con_los_centros(self):
        html = self._html()

        self.assertIn('<datalist id="centros-de-costo">', html)
        self.assertIn('<option value="700.50107">', html)

    def test_el_input_de_codigo_de_la_fila_lleva_el_attr_list(self):
        """El datalist sólo funciona si el input lo referencia con `list=`."""
        html = self._html()

        coincidencia = re.search(r'<input[^>]*name="cost_allocations-0-codigo"[^>]*>', html)
        self.assertIsNotNone(coincidencia, 'no está el input del código de la fila')
        self.assertIn('list="centros-de-costo"', coincidencia.group(0))

    def test_el_datalist_no_queda_dentro_del_cost_container(self):
        """`prefijarImputacion()` hace `innerHTML = ''` sobre `#cost-container`.

        Si el datalist quedara adentro, el primer cambio de suscripciones lo
        borraría y el campo dejaría de ofrecer el catálogo justo después de usarlo.
        """
        html = self._html()

        inicio = html.index('<div id="cost-container">')
        fragmento = html[inicio:]
        self.assertNotIn('id="centros-de-costo"', fragmento)

    def test_el_copy_invita_a_elegir_de_la_lista(self):
        html = self._html()

        self.assertIn('Centro de Costo', html)
        self.assertIn('debe sumar 100', html)
        # El copy viejo prometía precarga y no mencionaba la lista.
        self.assertNotIn('El centro se precarga desde el', html)

    def test_el_indicador_de_la_suma_es_server_rendered(self):
        """El total se informa en el HTML servido, no sólo cuando corre el JS.

        El operador escribe los porcentajes a mano y necesito ver la suma sin
        esperar a que el servidor rechace el POST: el elemento vive fuera de
        `#cost-container` para que la reconstrucción del reparto no lo borre.
        """
        html = self._html()

        coincidencia = re.search(r'<div[^>]*id="cost-total-indicador"[^>]*>', html)
        self.assertIsNotNone(coincidencia, 'no está el indicador de la suma')
        self.assertIn('role="status"', coincidencia.group(0))
        self.assertIn('aria-live="polite"', coincidencia.group(0))
        self.assertIn('id="cost-total-badge"', html)


class CentroFueraDelCatalogoTests(TestCase):
    """El `<datalist>` sugiere, no restringe: un centro nuevo se guarda igual.

    Las tres facturas reales del CMP se cargan por el camino manual con un solo
    ítem: la 182 a un centro al 100 %, la 279 a dos (90/10) y la 276 a tres
    (25/65/10) sobre esa única línea. El reparto no es derivable del ítem, así
    que estas pruebas confirman que sigue siendo la decisión del operador y que
    un centro ajeno al catálogo no se rechaza.
    """

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        company = CompanySettings.get_instance()
        company.registro_comercial = 'A54877'
        company.save(update_fields=['registro_comercial'])
        cls.admin = User.objects.create_superuser(
            username='fueracatalogo',
            email='fueracatalogo@example.com',
            password='pass',  # pragma: allowlist secret
            first_name='Admin',
            last_name='Fuera',
        )
        cls.customer = Customer.objects.create(
            client_type='juridica',
            user=User.objects.create_user(
                'fueracust',
                'fueracust@example.com',
                'pass',  # pragma: allowlist secret
                first_name='Cli',
                last_name='Fuera',
            ),
            company_name='Empresa Fuera S.A.',
            reeup=next_reeup(),
            nit=next_nit(),
            account='9001000000000020',
        )
        # Una jurídica sólo se factura dentro de la vigencia de un contrato. Los
        # ítems manuales de esta clase arrancan el 15/05/2026, así que el contrato
        # cubre todo 2026.
        Contract.objects.create(
            customer=cls.customer,
            number='C-CENTRO',
            start_date=date(2026, 1, 1),
            validity_years=2,
        )
        cls.service = Service.objects.create(
            user=cls.admin,
            title='Radar',
            summary='Monitoreo con radar',
            service_type=Service.COMMERCIAL,
            service_category='pronostico',
            code='700501072507005',
            price=Decimal('45.00'),
        )
        cls.url = reverse('commercial:factura_create')

    def setUp(self):
        huey.flush()
        self.addCleanup(huey.flush)
        self.client.force_login(self.admin)

    def _manual(self, filas):
        """Un solo ítem manual, con el reparto que se quiere probar."""
        datos = {
            'customer': self.customer.pk,
            'commercial_registry': 'REG-CENTRO',
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-service': str(self.service.pk),
            'items-0-cantidad': '4',
            'items-0-start_date': '2026-05-15',
            # El navegador manda lo derivado; `clean()` lo vuelve a sacar del
            # servicio. Sin `codigo` y `precio` la línea no valida.
            'items-0-codigo': self.service.code,
            'items-0-precio': str(self.service.price),
            'cost_allocations-TOTAL_FORMS': str(len(filas)),
            'cost_allocations-INITIAL_FORMS': '0',
            'cost_allocations-MIN_NUM_FORMS': '0',
            'cost_allocations-MAX_NUM_FORMS': '1000',
        }
        for indice, fila in enumerate(filas):
            datos[f'cost_allocations-{indice}-codigo'] = fila[0]
            datos[f'cost_allocations-{indice}-porcentaje'] = fila[1]
        return datos

    def _factura_creada(self):
        invoice = Invoice.objects.filter(customer=self.customer).order_by('-id').first()
        self.assertIsNotNone(invoice, 'no se creó ninguna factura para el cliente')
        return invoice

    def _reparto_guardado(self, invoice):
        return [(a.codigo, a.porcentaje) for a in invoice.cost_allocations.all()]

    def test_un_centro_fuera_del_catalogo_se_guarda_tal_cual(self):
        """Un centro nuevo (los de las facturas 276/279) no puede ser rechazado."""
        self.client.post(self.url, self._manual([('700.99999', '100.00')]))

        invoice = self._factura_creada()
        self.assertEqual(self._reparto_guardado(invoice), [('700.99999', Decimal('100.00'))])

    def test_el_reparto_de_un_centro_al_cien_por_ciento(self):
        """Factura real 182: un solo ítem, un solo centro al 100 %."""
        self.client.post(self.url, self._manual([('700.50107', '100.00')]))

        invoice = self._factura_creada()
        self.assertEqual(invoice.items.count(), 1)
        self.assertEqual(self._reparto_guardado(invoice), [('700.50107', Decimal('100.00'))])

    def test_el_reparto_de_dos_centros_noventa_diez(self):
        """Factura real 279: un solo ítem a dos centros 90/10."""
        self.client.post(self.url, self._manual([('700.50207', '90.00'), ('700.50407', '10.00')]))

        invoice = self._factura_creada()
        self.assertEqual(invoice.items.count(), 1)
        self.assertEqual(
            self._reparto_guardado(invoice),
            [('700.50207', Decimal('90.00')), ('700.50407', Decimal('10.00'))],
        )

    def test_el_reparto_de_tres_centros_sobre_un_solo_item(self):
        """Factura real 276: 25/65/10 sobre una única línea.

        El reparto no es derivable del ítem (una línea sola no produce tres
        porcentajes), así que este caso prueba que sigue siendo una decisión del
        operador y que la pantalla no la restringe al catálogo.
        """
        self.client.post(
            self.url,
            self._manual([('700.50107', '25.00'), ('700.50207', '65.00'), ('700.50407', '10.00')]),
        )

        invoice = self._factura_creada()
        self.assertEqual(invoice.items.count(), 1)
        self.assertEqual(
            self._reparto_guardado(invoice),
            [
                ('700.50107', Decimal('25.00')),
                ('700.50207', Decimal('65.00')),
                ('700.50407', Decimal('10.00')),
            ],
        )
