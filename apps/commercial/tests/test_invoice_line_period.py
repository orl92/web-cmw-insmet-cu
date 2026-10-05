"""Dos períodos, dos lugares: el del contrato y el facturado.

El formulario de facturación metía en una sola tarjeta titulada "Período de
Facturación" dos datos que no son el mismo dato:

- el **período del contrato** (`ServiceSubscription.start_date` + `quantity`),
  que es un hecho persistente entre el proveedor y el cliente, y
- el **período facturado** (`Invoice.period_label`), que es texto libre escrito
  por el operador e impreso en la factura.

Compartiendo tarjeta, el formulario no cerraba nunca. El caso real lo muestra:
agrometeo de mayo a julio y pronóstico desde el 10 de junio obligan a mentirle a
una de las dos líneas si las dos tienen que compartir una sola fecha.

`start_date` es un contrato: escribir una fecha que no es la real al crear la
suscripción la deja mal para siempre, y ninguna facturación posterior la
corrige. Por eso pasa a ser un campo de cada línea, con la fecha de la factura
como valor por defecto: el caso común es no tocarlo y el raro queda expresado.

La unidad de facturación no se guarda: se deriva de `service_category`, igual que
ya lo hacía `InvoiceItemForm.clean()` y `get_quantity_period_display()`. Un
selector de unidad duplicaría un dato que ya existe.
"""

import inspect
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.commercial.forms.invoice import InvoiceForm, InvoiceItemForm
from apps.commercial.models import Invoice, InvoiceItem, Service, ServiceSubscription
from apps.commercial.tests.factories import make_user, natural_customer
from apps.commercial.tests.test_views import _make_superuser
from apps.core.models import CompanySettings, SiteConfiguration
from config.huey import huey


class _FacturacionBase(TestCase):
    """Cliente, dos servicios comerciales y el formulario listo para postear."""

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        company = CompanySettings.get_instance()
        company.registro_comercial = 'A54877'
        company.save(update_fields=['registro_comercial'])

        cls.admin = _make_superuser('periodosadmin')
        cls.customer = natural_customer(make_user('periodoscust'))
        cls.agro = Service.objects.create(
            user=cls.admin,
            title='Agrometeorológico',
            summary='Pronóstico agrometeorológico',
            service_type=Service.COMMERCIAL,
            service_category='agrometeo',
            code='700501072507005',
            price=Decimal('100.00'),
        )
        cls.pronostico = Service.objects.create(
            user=cls.admin,
            title='Pronóstico diario',
            summary='Pronóstico puntual',
            service_type=Service.COMMERCIAL,
            service_category='pronostico',
            code='700502072507006',
            price=Decimal('5.00'),
        )
        cls.url_crear = reverse('commercial:factura_create')
        cls.url_ajax = reverse('commercial:ajax_pending_subscriptions')

    def setUp(self):
        # El POST encola la tarea real de PDF; la cola se vacía por corrida, no
        # por test, así que hay que limpiarla en los dos sentidos.
        huey.flush()
        self.addCleanup(huey.flush)
        self.client.force_login(self.admin)

    def _linea(self, index, service, cantidad, inicio):
        return {
            f'items-{index}-service': str(service.pk),
            f'items-{index}-cantidad': str(cantidad),
            f'items-{index}-start_date': inicio,
            # El navegador manda lo derivado; clean() lo vuelve a sacar del
            # servicio y el POST no puede fijar nada de esto.
            f'items-{index}-precio': '9999.99',
            f'items-{index}-unidad_medida': 'MES',
            f'items-{index}-codigo': 'HACKED',
        }

    def _imputacion(self):
        """Reparto mínimo válido: sin él el formset rechaza la factura entera."""
        return {
            'cost_allocations-TOTAL_FORMS': '1',
            'cost_allocations-INITIAL_FORMS': '0',
            'cost_allocations-MIN_NUM_FORMS': '0',
            'cost_allocations-MAX_NUM_FORMS': '1000',
            'cost_allocations-0-codigo': '700.50107',
            'cost_allocations-0-porcentaje': '100.00',
        }

    def _manual(self, lineas, **extra):
        datos = {
            'customer': self.customer.pk,
            'commercial_registry': 'REG-PERIODO',
            'items-TOTAL_FORMS': str(len(lineas)),
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
        }
        for linea in lineas:
            datos.update(linea)
        datos.update(self._imputacion())
        datos.update(extra)
        return datos

    def _suscripciones_creadas(self):
        return list(ServiceSubscription.objects.order_by('pk'))


class DosPeriodosEnLugaresDistintosTests(_FacturacionBase):
    """La tarjeta del período facturado queda con el texto y nada más."""

    def test_el_formulario_de_factura_no_tiene_fechas(self):
        """`start_date` y `end_date` no son de la factura: son de la línea."""
        campos = InvoiceForm().fields

        self.assertNotIn('start_date', campos)
        self.assertNotIn('end_date', campos)

    def test_el_periodo_impreso_sigue_en_el_formulario(self):
        """Lo que sí es de la factura se queda: el texto que va al PDF."""
        self.assertIn('period_label', InvoiceForm().fields)

    def test_la_pantalla_no_tiene_el_rango_de_fechas(self):
        html = self.client.get(self.url_crear).content.decode()

        self.assertNotIn('id_start_date', html)
        self.assertNotIn('id_end_date', html)

    def test_el_conteo_de_dias_desaparece(self):
        """`#days-count` nunca se posteó ni se guardó: era decoración JS."""
        html = self.client.get(self.url_crear).content.decode()

        self.assertNotIn('days-count', html)
        self.assertNotIn('Días del período', html)

    def test_el_periodo_impreso_se_ve_en_la_tarjeta(self):
        html = self.client.get(self.url_crear).content.decode()

        self.assertIn('name="period_label"', html)


class FechaDeInicioPorLineaTests(_FacturacionBase):
    """`start_date` es un campo de la línea, con la fecha de la factura por defecto."""

    def test_la_linea_tiene_fecha_de_inicio(self):
        self.assertIn('start_date', InvoiceItemForm().fields)

    def test_la_fecha_de_inicio_de_la_linea_es_obligatoria(self):
        """El contrato no se crea sin fecha: escribirla mal la deja mal para siempre."""
        campo = InvoiceItemForm().fields['start_date']

        self.assertTrue(campo.required)

    def test_la_linea_no_ofrece_un_selector_de_unidad(self):
        """La unidad se deriva de `service_category`; un selector la duplicaría."""
        self.assertEqual(
            set(InvoiceItemForm().fields),
            {'service', 'codigo', 'cantidad', 'unidad_medida', 'precio', 'start_date'},
        )

    def test_la_linea_acepta_el_formato_legible(self):
        form = InvoiceItemForm(
            data={
                'service': self.agro.pk,
                'cantidad': 3,
                'precio': '100.00',
                'unidad_medida': 'U',
                'start_date': '15/05/2026',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['start_date'], date(2026, 5, 15))

    def test_la_linea_acepta_el_formato_iso(self):
        form = InvoiceItemForm(
            data={
                'service': self.agro.pk,
                'cantidad': 3,
                'precio': '100.00',
                'unidad_medida': 'U',
                'start_date': '2026-05-15',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['start_date'], date(2026, 5, 15))

    def test_la_linea_rechaza_una_fecha_que_no_se_entiende(self):
        """Sin rango que la sugiera, la fecha tiene que estar bien escrita."""
        form = InvoiceItemForm(
            data={
                'service': self.agro.pk,
                'cantidad': 3,
                'precio': '100.00',
                'unidad_medida': 'U',
                'start_date': 'el 15 de mayo',
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('start_date', form.errors)

    def test_la_fecha_por_defecto_es_la_fecha_de_la_factura(self):
        """El caso común es no tocar nada: la línea ya arranca en la fecha de hoy."""
        with patch('django.utils.timezone.localdate', return_value=date(2026, 5, 15)):
            response = self.client.get(self.url_crear)

        formset = response.context['items_formset']
        self.assertEqual(formset.forms[0]['start_date'].value(), '2026-05-15')

    def test_la_fecha_por_defecto_se_ve_en_la_linea(self):
        html = self.client.get(self.url_crear).content.decode()

        self.assertIn('id_items-0-start_date', html)

    def test_cada_linea_nueva_arranca_en_la_fecha_de_la_factura(self):
        """Una sola fila, con la fecha puesta: ni rango global ni fila en blanco.

        El navegador clona la última fila para agregar líneas, así que la fila
        inicial tiene que ser una y venir con la fecha: una fila de más aparece
        vacía y su `start_date` requerido manda el formulario de vuelta.
        """
        with patch('django.utils.timezone.localdate', return_value=date(2026, 5, 15)):
            response = self.client.get(self.url_crear)

        formset = response.context['items_formset']
        self.assertEqual(len(formset.forms), 1)
        self.assertEqual(formset.forms[0]['start_date'].value(), '2026-05-15')


class ElCasoRealTests(_FacturacionBase):
    """Agrometeo de mayo a julio y pronóstico desde el 10 de junio."""

    def test_dos_lineas_guardan_cada_una_su_propio_inicio(self):
        response = self.client.post(
            self.url_crear,
            self._manual(
                [
                    self._linea(0, self.agro, 3, '2026-05-15'),
                    self._linea(1, self.pronostico, 10, '2026-06-10'),
                ]
            ),
        )

        self.assertEqual(response.status_code, 302)
        subs = self._suscripciones_creadas()
        self.assertEqual(len(subs), 2)
        self.assertEqual(subs[0].start_date.date(), date(2026, 5, 15))
        self.assertEqual(subs[1].start_date.date(), date(2026, 6, 10))

    def test_la_unidad_se_deriva_del_servicio_y_no_del_post(self):
        """La línea manda `unidad_medida='MES'` para las dos: no puede ganarle."""
        self.client.post(
            self.url_crear,
            self._manual(
                [
                    self._linea(0, self.agro, 3, '2026-05-15'),
                    self._linea(1, self.pronostico, 10, '2026-06-10'),
                ]
            ),
        )

        unidades = sorted(InvoiceItem.objects.values_list('unidad_medida', flat=True))
        self.assertEqual(unidades, ['DÍA', 'MES'])

    def test_una_linea_sin_fecha_no_crea_la_suscripcion(self):
        linea = self._linea(0, self.agro, 3, '2026-05-15')
        del linea['items-0-start_date']

        response = self.client.post(self.url_crear, self._manual([linea]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ServiceSubscription.objects.count(), 0)
        self.assertContains(response, 'items-0-start_date')

    def test_la_factura_creada_es_una_sola(self):
        self.client.post(
            self.url_crear,
            self._manual(
                [
                    self._linea(0, self.agro, 3, '2026-05-15'),
                    self._linea(1, self.pronostico, 10, '2026-06-10'),
                ]
            ),
        )

        self.assertEqual(Invoice.objects.filter(customer=self.customer).count(), 1)
        self.assertEqual(InvoiceItem.objects.count(), 2)


class PeriodoDeLoteReadOnlyTests(_FacturacionBase):
    """En lote el período se muestra: es un dato que la suscripción ya tiene."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sub = ServiceSubscription.objects.create(
            customer=cls.customer,
            service=cls.pronostico,
            start_date=timezone.make_aware(datetime(2026, 5, 15, 8, 0)),
            quantity=3,
            payment_status='requested',
        )

    def test_el_lote_muestra_el_periodo_de_cada_suscripcion(self):
        """Pronóstico: días, que es lo que la categoría del servicio implica."""
        response = self.client.get(self.url_ajax, {'customer': self.customer.pk})

        self.assertContains(response, 'data-periodo="desde 15/05/2026 · 3 días"')

    def test_el_lote_usa_meses_para_un_servicio_agrometeo(self):
        """La misma línea de código dice "meses" u "ó días" según el servicio."""
        ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.agro,
            start_date=timezone.make_aware(datetime(2026, 5, 15, 8, 0)),
            quantity=3,
            payment_status='requested',
        )

        response = self.client.get(self.url_ajax, {'customer': self.customer.pk})

        self.assertContains(response, 'data-periodo="desde 15/05/2026 · 3 meses"')

    def test_el_periodo_del_lote_no_es_un_campo_que_se_edaite(self):
        """Lo único que la pantalla manda de cada suscripción es la casilla."""
        response = self.client.get(self.url_ajax, {'customer': self.customer.pk})

        html = response.content.decode()
        self.assertEqual(html.count('<input'), 1)
        self.assertNotIn('data-start=', html)


class FlashDelPeriodoTests(_FacturacionBase):
    """El flash anuncia el período facturado, no un rango que el PDF no imprime."""

    def _mensajes(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]

    def _lote(self, period_label):
        self.sub = ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.agro,
            start_date=timezone.make_aware(datetime(2025, 9, 1, 8, 0)),
            quantity=3,
            payment_status='requested',
        )
        return self.client.post(
            self.url_crear,
            {
                'customer': self.customer.pk,
                'commercial_registry': 'REG-FLASH',
                'period_label': period_label,
                'subscriptions': [str(self.sub.pk)],
                **self._imputacion(),
            },
        )

    def test_el_flash_anuncia_el_periodo_que_escribio_el_operador(self):
        response = self._lote('Mes de mayo y junio de 2025')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            any('Mes de mayo y junio de 2025' in m for m in self._mensajes(response)),
            f'mensajes: {self._mensajes(response)}',
        )

    def test_el_flash_no_anuncia_un_rango_de_fechas(self):
        """T2 dejó de imprimir "Desde X hasta Y": el flash tampoco puede hacerlo."""
        response = self._lote('Mes de mayo y junio de 2025')
        self.assertEqual(response.status_code, 302)

        joined = ' '.join(self._mensajes(response))
        self.assertNotIn(' - ', joined)

    def test_el_periodo_escrito_queda_guardado_en_la_factura(self):
        """Sin esto el PDF no podría imprimir lo que el operador escribió."""
        self._lote('Mes de mayo y junio de 2025')

        invoice = Invoice.objects.get(customer=self.customer)
        self.assertEqual(invoice.period_label, 'Mes de mayo y junio de 2025')

    def test_sin_periodo_escrito_el_flash_anuncia_la_fecha_de_emision(self):
        response = self._lote('')

        invoice = Invoice.objects.get(customer=self.customer)
        self.assertTrue(
            any(invoice.issue_date.strftime('%d/%m/%Y') in m for m in self._mensajes(response)),
            f'mensajes: {self._mensajes(response)}',
        )

    def test_el_periodo_escrito_tambien_se_guarda_en_una_factura_manual(self):
        """El PDF se arma desde `period_label`: sin esto saldría la fecha de emisión."""
        self.client.post(
            self.url_crear,
            self._manual(
                [self._linea(0, self.agro, 3, '2026-05-15')],
                period_label='Mes de mayo de 2026',
            ),
        )

        invoice = Invoice.objects.get(customer=self.customer)
        self.assertEqual(invoice.period_label, 'Mes de mayo de 2026')


class BatchSinFechasMuertasTests(_FacturacionBase):
    """`start_date`/`end_date` no se usaban: quedaban en la firma y en ningún lado más."""

    def test_process_batch_invoice_no_declara_fechas(self):
        from apps.commercial.views.invoices import InvoiceCreateView

        parametros = inspect.signature(InvoiceCreateView.process_batch_invoice).parameters

        self.assertNotIn('start_date', parametros)
        self.assertNotIn('end_date', parametros)

    def test_process_manual_invoice_no_declara_fechas(self):
        """El inicio llega por línea: la factura ya no lo pasa entero."""
        from apps.commercial.views.invoices import InvoiceCreateView

        parametros = inspect.signature(InvoiceCreateView.process_manual_invoice).parameters

        self.assertNotIn('start_date', parametros)
        self.assertNotIn('end_date', parametros)

    def test_facturar_en_lote_no_toca_el_inicio_de_la_suscripcion(self):
        """El período del contrato es de la suscripción, no de la factura."""
        elegido = timezone.make_aware(datetime(2025, 5, 15, 8, 0))
        sub = ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.agro,
            start_date=elegido,
            quantity=3,
            payment_status='requested',
        )

        self.client.post(
            self.url_crear,
            {
                'customer': self.customer.pk,
                'commercial_registry': 'REG-LOTE',
                'period_label': 'Mes de mayo y junio de 2025',
                'subscriptions': [str(sub.pk)],
                **self._imputacion(),
            },
        )

        sub.refresh_from_db()
        self.assertEqual(sub.start_date, elegido)
        self.assertEqual(sub.payment_status, 'pending')

    def test_un_post_con_las_fechas_viejas_se_ignora(self):
        """Una pestaña vieja o un script con el payload anterior no rompe nada."""
        elegido = timezone.make_aware(datetime(2025, 5, 15, 8, 0))
        sub = ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.agro,
            start_date=elegido,
            quantity=3,
            payment_status='requested',
        )

        response = self.client.post(
            self.url_crear,
            {
                'customer': self.customer.pk,
                'commercial_registry': 'REG-LOTE-VIEJO',
                'period_label': 'Mayo 2026',
                'start_date': '01/05/2026',
                'end_date': '31/05/2026',
                'subscriptions': [str(sub.pk)],
                **self._imputacion(),
            },
        )

        self.assertEqual(response.status_code, 302)
        sub.refresh_from_db()
        self.assertEqual(sub.start_date, elegido)
        self.assertEqual(Invoice.objects.get(customer=self.customer).period_label, 'Mayo 2026')
