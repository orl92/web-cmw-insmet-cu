"""El período facturado sale de las líneas; el del contrato vive en la suscripción.

El formulario de facturación metía en una sola tarjeta titulada "Período de
Facturación" dos datos que no son el mismo dato:

- el **período del contrato** (`ServiceSubscription.start_date` + `quantity`),
  que es un hecho persistente entre el proveedor y el cliente, y
- el **período facturado** (`Invoice.period_start` + `Invoice.period_end`, el
  rango que el PDF convierte en frase), que ya no se elige y que la vista
  agrupa en facturas separadas cuando las suscripciones de un lote no comparten
  meses.

Compartiendo tarjeta, el formulario no cerraba nunca. El caso real lo muestra:
agrometeo de mayo a julio y pronóstico desde el 10 de junio obligan a mentirle a
una de las dos líneas si las dos tienen que compartir una sola fecha.

`start_date` es un contrato: escribir una fecha que no es la real al crear la
suscripción la deja mal para siempre, y ninguna facturación posterior la
corrige. Por eso pasa a ser un campo de cada línea, con la fecha de hoy
como valor por defecto: el caso común es no tocarlo y el raro queda expresado.

La unidad de facturación no se guarda: se deriva de `service_category`, igual que
ya lo hacía `InvoiceItemForm.clean()` y `get_quantity_period_display()`. Un
selector de unidad duplicaría un dato que ya existe.

El período facturado tampoco se declara: se deduce de las líneas, igual que en el
lote se deduce de cada suscripción. Cada línea aporta los meses de su servicio
—`agrometeo` cuenta meses desde el de inicio, `pronostico` cuenta días— y la
factura cubre del mes más viejo al más nuevo. Así los dos caminos contestan lo
mismo, y no queda forma de declarar un período que las líneas no respalden: era
justo eso lo que hacía imposible facturar un servicio que empezó meses atrás.
"""

import json
import re
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.commercial.forms.invoice import InvoiceForm, InvoiceItemForm, InvoiceItemFormSet
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
            # servicio y el POST no puede fijar nada de esto. `unidad_medida` es el
            # caso interesante: ya no hay campo con ese nombre, así que viaja como
            # una clave que el formulario ignora por completo.
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
        # El período no viaja en el POST: sale de las líneas de abajo. Lo que se
        # prueba acá es el período *del contrato*, línea por línea, y la deducción
        # del período facturado; la regla "toda línea cae dentro del período" dejó
        # de poder violarse desde el formulario.
        for linea in lineas:
            datos.update(linea)
        datos.update(self._imputacion())
        datos.update(extra)
        return datos

    def _suscripciones_creadas(self):
        return list(ServiceSubscription.objects.order_by('pk'))


class PeriodoDerivadoTests(_FacturacionBase):
    """El período facturado se reporta a partir de las líneas: no se declara."""

    def test_el_formulario_no_declara_ningun_mes(self):
        """Los tres selects se fueron: elegir el período ya no es una entrada."""
        campos = InvoiceForm().fields

        for nombre in ('month_from', 'year', 'month_to', 'period_label', 'period_months'):
            self.assertNotIn(nombre, campos)

    def test_la_tarjeta_muestra_el_periodo_en_vez_de_pedirlo(self):
        """En su lugar hay dónde leerlo; ningún control para escribirlo."""
        html = self.client.get(self.url_crear).content.decode()

        self.assertIn('id="periodo-derivado"', html)
        for nombre in ('month_from', 'year', 'month_to'):
            self.assertNotIn(f'name="{nombre}"', html)


class FechaDeInicioPorLineaTests(_FacturacionBase):
    """`start_date` es un campo de la línea, con la fecha de la factura por defecto."""

    def test_la_linea_tiene_fecha_de_inicio(self):
        self.assertIn('start_date', InvoiceItemForm().fields)

    def test_la_fecha_de_inicio_de_la_linea_es_obligatoria(self):
        """El contrato no se crea sin fecha: escribirla mal la deja mal para siempre."""
        campo = InvoiceItemForm().fields['start_date']

        self.assertTrue(campo.required)

    def test_la_linea_no_ofrece_un_selector_de_unidad(self):
        """La unidad no es un dato de la línea: la nombra el rótulo de `cantidad`.

        `unidad_medida` tampoco está, y a propósito. Un campo `readonly` que siempre
        dice `U` ocuparía una columna para repetir el `default='U'` del modelo, y
        obligaría a conservar el código que lo reescribía con `MES`/`DÍA`.
        """
        self.assertEqual(
            set(InvoiceItemForm().fields),
            {'service', 'codigo', 'cantidad', 'precio', 'start_date'},
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

    def test_el_periodo_no_se_declara_por_url(self):
        """Los meses en la query string no son una entrada del formulario.

        Antes estos parámetros elegían el período y hasta movían la fecha de la
        línea; ahora se ignoran, y la línea sigue arrancando hoy.
        """
        with patch('django.utils.timezone.localdate', return_value=date(2026, 5, 15)):
            response = self.client.get(
                self.url_crear, {'year': '2026', 'month_from': '1', 'month_to': '3'}
            )

        formset = response.context['items_formset']
        self.assertEqual(formset.forms[0]['start_date'].value(), '2026-05-15')

    def test_una_linea_de_un_mes_pasado_se_factura_ese_mes(self):
        """El caso que el período declarado hacía imposible.

        Facturar un servicio que empezó en enero: la línea trae su fecha, y la
        factura cubre el mes de la línea y los que su cantidad alcance. Antes el
        POST moría en "ese día está fuera del período facturado".
        """
        response = self.client.post(
            self.url_crear,
            self._manual([self._linea(0, self.agro, 3, '2026-01-05')]),
        )

        self.assertEqual(response.status_code, 302)
        invoice = Invoice.objects.get(customer=self.customer)
        self.assertEqual(invoice.period_start, date(2026, 1, 1))
        self.assertEqual(invoice.period_end, date(2026, 3, 31))


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

    def test_la_unidad_de_medida_no_sale_del_post_ni_de_la_categoria(self):
        """Las dos líneas mandan `unidad_medida='MES'`; queda `U` en las dos.

        La columna `U/M` de las facturas reales del CMP no dice `MES` ni `DÍA` en
        ningún lado: dice `U` o nada, con cantidades de 30, 31, 2 y 4. La unidad de
        la fila la nombra el rótulo de `cantidad`, así que aquí no hay nada que
        derivar: el `default='U'` del modelo manda y el POST no tiene campo por el
        que ganarle.
        """
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
        self.assertEqual(unidades, ['U', 'U'])

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

    def test_la_descripcion_es_el_titulo_del_servicio_y_no_un_titulo_con_sufijo(self):
        """La factura manual escribe el título del catálogo, sin pegarle nada.

        El "por meses" de la 279 es parte del nombre del servicio en el catálogo,
        no un sufijo que el sistema agrega: las facturas de pronóstico (182 y 276)
        no lo tienen. Este es el test que lo verifica de punta a punta, porque acá
        sí pasa por `process_manual_invoice`, que es donde una descripción podría
        inventarse.
        """
        self.client.post(
            self.url_crear,
            self._manual(
                [
                    self._linea(0, self.agro, 2, '2026-05-15'),
                    self._linea(1, self.pronostico, 4, '2026-06-10'),
                ]
            ),
        )

        self.assertEqual(
            sorted(InvoiceItem.objects.values_list('descripcion', flat=True)),
            sorted([self.agro.title, self.pronostico.title]),
        )

    def test_la_unidad_medida_vale_u_y_la_cantidad_la_escribe_el_operador(self):
        """`U/M` = `U` en las dos, con las cantidades que puso el operador.

        Las cantidades reales son 30, 31, 2 y 4: el número de días del mes o de
        meses del agrometeo. Por eso `U/M` no dice nada y el rótulo de `cantidad` la
        nombra.
        """
        self.client.post(
            self.url_crear,
            self._manual(
                [
                    self._linea(0, self.agro, 2, '2026-05-15'),
                    self._linea(1, self.pronostico, 31, '2026-06-10'),
                ]
            ),
        )

        self.assertEqual(
            sorted(InvoiceItem.objects.values_list('cantidad', 'unidad_medida')),
            [(2, 'U'), (31, 'U')],
        )


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

    def test_el_periodo_del_lote_no_es_un_campo_que_se_edite(self):
        """Lo único que la pantalla manda de cada suscripción es la casilla."""
        response = self.client.get(self.url_ajax, {'customer': self.customer.pk})

        html = response.content.decode()
        self.assertEqual(html.count('<input'), 1)
        self.assertNotIn('data-start=', html)


class ElRotuloDiceLaUnidadTests(_FacturacionBase):
    """La unidad de `cantidad` se lee en el rótulo, y sólo en el rótulo.

    Las tres facturas reales del CMP muestran por qué: su columna `U/M` nunca
    dice `MES` ni `DÍA`, dice `U` o nada. Con `U/M` neutra, el rótulo de la
    cantidad es el único lugar donde el operador lee si está escribiendo meses o
    días, así que es parte del contrato del campo y no decoración. Antes de T4 esa
    columna decía `MES` o `DÍA` según la categoría, y entonces el rótulo no
    agregaba nada; hoy `U/M` no dice nada y el rótulo carga con la unidad entera.

    Y la unidad no es un dato propio: sale de `service_category` (agrometeo
    factura meses, todo lo demás días), igual que ya rotulaba `SubscriptionForm`.
    Por eso el rótulo se resuelve en el servidor y no sólo después de que corra el
    JavaScript: una fila que vuelve a renderizarse por un error de validación se
    rotula igual sin haber ejecutado una línea de script.

    `cantidad` no trae valor por defecto. Las cantidades observadas son 30, 31,
    2 y 4 —el número de días de mayo y junio, o el de meses de un agrometeo— y
    nunca 1: un número inventado en este campo subfactura en silencio.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Fuera del queryset del campo: un POST con esta fila tiene que quedar
        # neutra, no reventar el render ni rotular con la categoría de un
        # servicio que la pantalla no ofrece.
        cls.baja = Service.objects.create(
            user=cls.admin,
            title='Agrometeorológico dado de baja',
            summary='Retirado de la oferta',
            service_type=Service.COMMERCIAL,
            service_category='agrometeo',
            code='700501072507007',
            price=Decimal('100.00'),
            record_active=False,
        )

    def _formset(self, **linea):
        datos = {
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
        }
        datos.update(linea)
        # El prefijo es el de la vista: sin él el formset no encuentra su propio
        # management form y se queda sin filas.
        return InvoiceItemFormSet(data=datos, prefix='items')

    def _rotulo_renderizado(self, html, indice=0):
        """Texto del `<label>` de la cantidad, y nada más.

        Buscar la cadena suelta no sirve: la vieja ayuda "Cantidad de meses o
        días según el tipo de servicio." hacía que un `assertContains` pasara con
        el rótulo todavía en `Cantidad`. Lo que dice la unidad es el `<label>`.
        """
        coincidencia = re.search(
            rf'<label[^>]*for="id_items-{indice}-cantidad"[^>]*>(.*?)</label>', html, re.S
        )
        self.assertIsNotNone(coincidencia, 'el rótulo de la cantidad no está en el HTML')
        return coincidencia.group(1).strip()

    def test_el_rotulo_de_una_linea_agrometeo_dice_meses(self):
        formset = self._formset(**{'items-0-service': str(self.agro.pk)})

        self.assertEqual(formset.forms[0]['cantidad'].label, 'Cantidad de meses')

    def test_el_rotulo_de_una_linea_no_agrometeo_dice_dias(self):
        """Pronóstico factura por días: mismo campo, otra unidad."""
        formset = self._formset(**{'items-0-service': str(self.pronostico.pk)})

        self.assertEqual(formset.forms[0]['cantidad'].label, 'Cantidad de días')

    def test_el_rotulo_es_neutro_sin_servicio_elegido(self):
        """Sin servicio no hay unidad que nombrar: la pantalla inicial no puede inventarla."""
        formset = InvoiceItemFormSet()

        self.assertEqual(formset.forms[0]['cantidad'].label, 'Cantidad')

    def test_cada_linea_rotula_por_su_propio_servicio(self):
        """La unidad es de la fila, no de la factura: dos filas, dos rótulos."""
        formset = InvoiceItemFormSet(
            data={
                'items-TOTAL_FORMS': '2',
                'items-INITIAL_FORMS': '0',
                'items-MIN_NUM_FORMS': '0',
                'items-MAX_NUM_FORMS': '1000',
                'items-0-service': str(self.agro.pk),
                'items-1-service': str(self.pronostico.pk),
            },
            prefix='items',
        )

        self.assertEqual(formset.forms[0]['cantidad'].label, 'Cantidad de meses')
        self.assertEqual(formset.forms[1]['cantidad'].label, 'Cantidad de días')

    def test_el_rotulo_no_falla_con_un_servicio_inventado(self):
        """Una pestaña vieja o un POST a mano no rompen el render."""
        formset = self._formset(**{'items-0-service': 'no-existe'})

        self.assertEqual(formset.forms[0]['cantidad'].label, 'Cantidad')

    def test_el_rotulo_no_usa_un_servicio_dado_de_baja(self):
        """Fuera del queryset no cuenta: la pantalla no lo ofrece, así que no rotula."""
        formset = self._formset(**{'items-0-service': str(self.baja.pk)})

        self.assertEqual(formset.forms[0]['cantidad'].label, 'Cantidad')

    def test_el_rotulo_ya_dice_los_meses_sin_javascript(self):
        """Re-render por error de validación: el rótulo ya viene resuelto del servidor."""
        response = self.client.post(
            self.url_crear,
            self._manual([self._linea(0, self.agro, '', '2026-05-15')]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._rotulo_renderizado(response.content.decode()), 'Cantidad de meses')

    def test_el_rotulo_ya_dice_los_dias_sin_javascript(self):
        response = self.client.post(
            self.url_crear,
            self._manual([self._linea(0, self.pronostico, '', '2026-05-15')]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._rotulo_renderizado(response.content.decode()), 'Cantidad de días')

    def test_la_pantalla_limpia_no_promete_ninguna_unidad(self):
        """Al abrir el formulario todavía no hay servicio: no hay unidad que prometer."""
        html = self.client.get(self.url_crear).content.decode()

        self.assertEqual(self._rotulo_renderizado(html), 'Cantidad')

    def test_la_ayuda_redundante_no_se_imprime(self):
        """La ayuda repetía la unidad mientras el rótulo ya la resolvió.

        Se comprueba el `aria-describedby` y no el texto viejo: es la prueba
        estructural de que el campo quedó sin `help_text`, y no depende de cómo
        estuviera escrito. En el GET limpio no aparece ninguno; al re-renderizar
        el error, sólo queda el id del error.
        """
        limpio = self.client.get(self.url_crear).content.decode()
        self.assertNotIn('_cantidad_helptext', limpio)
        self.assertNotIn('aria-describedby="id_items-0-cantidad', limpio)

        response = self.client.post(
            self.url_crear,
            self._manual([self._linea(0, self.agro, '', '2026-05-15')]),
        )
        con_error = response.content.decode()
        self.assertNotIn('_cantidad_helptext', con_error)
        self.assertIn('aria-describedby="id_items-0-cantidad_error"', con_error)

    def test_cantidad_no_trae_valor_por_defecto(self):
        """Nada de `initial`, `default`, placeholder ni prellenado: lo escribe el operador."""
        form = InvoiceItemFormSet().forms[0]
        campo = form.fields['cantidad']

        self.assertFalse(campo.initial)
        self.assertNotIn('value=', campo.widget.render('cantidad', None, attrs={'id': 'x'}))
        self.assertNotIn('placeholder', str(campo.widget.attrs))

    def test_cantidad_sigue_obligatoria_y_el_futuro_numero_no_la_pasa(self):
        form = InvoiceItemForm(
            data={
                'service': self.pronostico.pk,
                'precio': '5.00',
                'unidad_medida': 'U',
                'start_date': '2026-05-15',
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('cantidad', form.errors)
        self.assertTrue(form.fields['cantidad'].required)
        self.assertEqual(form.fields['cantidad'].min_value, 1)

    def test_el_texto_de_ayuda_ya_no_repite_la_unidad(self):
        """Con el rótulo resolviéndola, la ayuda sobra: repetía "meses o días"."""
        self.assertEqual(InvoiceItemForm().fields['cantidad'].help_text, '')

    def test_el_javascript_recibe_la_categoria_que_define_la_unidad(self):
        """Guarda del contrato del script: sin `service_category` no puede rotular.

        Es el dato que el JavaScript necesita para mover el rótulo, y el que la
        vista ya serializa. El rótulo en sí lo escribe el script y eso no se
        prueba acá: no hay navegador en la suite.
        """
        response = self.client.get(self.url_crear)

        categorias = {
            s['id']: s['service_category']
            for s in json.loads(response.context['commercial_services_json'])
        }

        self.assertEqual(categorias[self.agro.pk], 'agrometeo')
        self.assertEqual(categorias[self.pronostico.pk], 'pronostico')

    def test_el_rotulo_de_la_cantidad_tiene_el_gancho_que_busca_el_script(self):
        """El `for` del `<label>` es lo que permite al script encontrarlo por fila."""
        html = self.client.get(self.url_crear).content.decode()

        self.assertIn('for="id_items-0-cantidad"', html)
        self.assertIn('label[for$="-cantidad"]', html)


class FlashDelPeriodoTests(_FacturacionBase):
    """El flash anuncia el período deducido, no un rango que el PDF no imprime."""

    def _mensajes(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]

    def _lote(self, inicio=datetime(2025, 5, 15, 8, 0), cantidad=3, **extra):
        self.sub = ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.agro,
            start_date=timezone.make_aware(inicio),
            quantity=cantidad,
            payment_status='requested',
        )
        return self.client.post(
            self.url_crear,
            {
                'customer': self.customer.pk,
                'commercial_registry': 'REG-FLASH',
                # El período del lote no viaja en el POST: sale de la fecha de
                # inicio y la cantidad de cada suscripción.
                'subscriptions': [str(self.sub.pk)],
                **self._imputacion(),
                **extra,
            },
        )

    def test_el_flash_anuncia_el_periodo_deducido_de_la_suscripcion(self):
        """Mayo con cantidad 3 ocupa mayo, junio y julio: eso imprime el PDF."""
        response = self._lote()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            any('De mayo a julio de 2025' in m for m in self._mensajes(response)),
            f'mensajes: {self._mensajes(response)}',
        )

    def test_el_flash_no_anuncia_un_rango_de_fechas(self):
        """T2 dejó de imprimir "Desde X hasta Y": el flash tampoco puede hacerlo."""
        response = self._lote()

        self.assertEqual(response.status_code, 302)
        self.assertNotIn(' - ', ' '.join(self._mensajes(response)))

    def test_el_periodo_deducido_queda_guardado_en_la_factura(self):
        """Sin el rango en la base el PDF no podría imprimir la frase."""
        self._lote()

        invoice = Invoice.objects.get(customer=self.customer)
        self.assertEqual(invoice.period_label, 'De mayo a julio de 2025')

    def test_el_periodo_del_lote_sale_solo_de_la_suscripcion(self):
        """Una sola cosa lo determina: el inicio y la cantidad de la suscripción."""
        response = self._lote(cantidad=1)

        self.assertEqual(response.status_code, 302)
        invoice = Invoice.objects.get(customer=self.customer)
        self.assertEqual(invoice.period_label, 'Mes de mayo de 2025')

    def test_el_periodo_de_una_factura_manual_sale_de_sus_lineas(self):
        """El PDF se arma desde el rango: sin esto saldría la fecha de emisión."""
        self.client.post(
            self.url_crear,
            self._manual([self._linea(0, self.agro, 3, '2026-05-15')]),
        )

        invoice = Invoice.objects.get(customer=self.customer)
        self.assertEqual(invoice.period_label, 'De mayo a julio de 2026')

    def test_una_linea_manual_de_un_mes_pasado_factura_ese_mes(self):
        """Ya no existe "fuera del período": el período lo fija la propia línea."""
        response = self.client.post(
            self.url_crear,
            self._manual([self._linea(0, self.agro, 3, '2026-08-15')]),
        )

        self.assertEqual(response.status_code, 302)
        invoice = Invoice.objects.get(customer=self.customer)
        self.assertEqual(invoice.period_label, 'De agosto a octubre de 2026')


class BatchSinFechasMuertasTests(_FacturacionBase):
    """En lote el período sale de cada suscripción: la factura no toca su inicio."""

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
                'subscriptions': [str(sub.pk)],
                **self._imputacion(),
            },
        )

        sub.refresh_from_db()
        self.assertEqual(sub.start_date, elegido)
        self.assertEqual(sub.payment_status, 'pending')


class LoteAgrupadoPorPeriodoTests(_FacturacionBase):
    """Una factura por grupo de meses, no una sola para todo el lote."""

    def _sub(self, inicio, cantidad=1, service=None):
        return ServiceSubscription.objects.create(
            customer=self.customer,
            service=service or self.agro,
            start_date=timezone.make_aware(inicio),
            quantity=cantidad,
            payment_status='requested',
        )

    def _lote(self, subs):
        return self.client.post(
            self.url_crear,
            {
                'customer': self.customer.pk,
                'commercial_registry': 'REG-GRUPO',
                # En lote no se envía período: la vista lo descarta y agrupa por
                # el de cada suscripción.
                'subscriptions': [str(sub.pk) for sub in subs],
                **self._imputacion(),
            },
        )

    @staticmethod
    def _meses_de(factura):
        """Los (año, mes) que abarca el rango de una factura."""
        year, month = factura.period_start.year, factura.period_start.month
        fin = (factura.period_end.year, factura.period_end.month)
        meses = []
        while (year, month) <= fin:
            meses.append((year, month))
            month += 1
            if month == 13:
                year, month = year + 1, 1
        return set(meses)

    def test_suscripciones_del_mismo_periodo_comparten_factura(self):
        mayo_a = self._sub(datetime(2025, 5, 10, 8, 0), cantidad=2)
        mayo_b = self._sub(datetime(2025, 5, 28, 8, 0), cantidad=2)

        self._lote([mayo_a, mayo_b])

        facturas = Invoice.objects.filter(customer=self.customer)
        self.assertEqual(facturas.count(), 1)
        self.assertEqual(facturas.get().period_label, 'De mayo a junio de 2025')
        self.assertEqual(facturas.get().items.count(), 2)

    def test_suscripciones_de_periodos_distintos_van_a_facturas_distintas(self):
        mayo = self._sub(datetime(2025, 5, 10, 8, 0), cantidad=2)
        julio = self._sub(datetime(2025, 7, 10, 8, 0), cantidad=1)

        self._lote([mayo, julio])

        labels = sorted(Invoice.objects.filter(customer=self.customer).values_list('pk', flat=True))
        self.assertEqual(len(labels), 2)
        periodos = {
            factura.period_label for factura in Invoice.objects.filter(customer=self.customer)
        }
        self.assertEqual(periodos, {'De mayo a junio de 2025', 'Mes de julio de 2025'})

    def test_cada_linea_cae_en_el_periodo_de_su_factura(self):
        """La regla del modelo se cumple por grupo, no sólo en el caso de una factura."""
        mayo = self._sub(datetime(2025, 5, 10, 8, 0), cantidad=2)
        julio = self._sub(datetime(2025, 7, 10, 8, 0), cantidad=1)

        self._lote([mayo, julio])

        for factura in Invoice.objects.filter(customer=self.customer):
            meses = self._meses_de(factura)
            for item in factura.items.all():
                inicio = timezone.localtime(item.subscription.start_date).date()
                self.assertIn((inicio.year, inicio.month), meses)

    def test_un_pronostico_que_cruza_el_mes_ocupa_los_dos(self):
        """A diferencia de `agrometeo`, acá la unidad son días, no meses."""
        pronostico = Service.objects.create(
            user=self.admin,
            title='Pronóstico',
            summary='Pronóstico diario',
            service_type=Service.COMMERCIAL,
            service_category='pronostico',
            code='700501072507006',
            price=Decimal('50.00'),
        )
        sub = self._sub(datetime(2025, 6, 20, 8, 0), cantidad=20, service=pronostico)

        self._lote([sub])

        factura = Invoice.objects.get(customer=self.customer)
        self.assertEqual(factura.period_label, 'De junio a julio de 2025')
