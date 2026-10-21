"""El centro de costo de la imputación se resuelve una sola vez: en el servidor.

La pantalla de factura arma el reparto a partir de los servicios que se están
facturando. Durante un tiempo esa regla del prefijo (`700501072507005` →
`700.50107`) estaba escrita dos veces —en `_centro_de_costo_de_codigo` y en
`centroDeCostoDeCodigo`, del JS inline de `create.html`— y dos copias de la
misma regla se pueden separar: el navegador podía proponer un centro que el
servidor no reconocía, o ninguno. Este módulo fija que el centro viaja
resuelto desde el servidor en las dos fuentes que alimentan la imputación
en vivo:

1. `commercial_services_json`, que alimenta el `servicesMap` de la
   facturación manual, y
2. `ajax_pending_subscriptions`, cuyo `data-centro` alimenta la facturación
   por lote.

Fija también la estructura del formulario: la tarjeta de imputación tiene que
quedar FUERA de `#manual-container` (si no, en el lote se envía a ciegas y el
operador no puede hacer el único paso que quiere hacer a mano), y el
`management_form` y el `<datalist>` tienen que quedar FUERA de
`#cost-container` (el JS borra el `innerHTML` de ese contenedor en cada
reconstrucción; si el management form estuviera adentro, el POST perdería el
`TOTAL_FORMS` y el formset se rompería).
"""

import json
import re
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.commercial.models import Customer, Service, ServiceSubscription

# El checkbox del lote se arma con varios atributos en varias líneas: para
# afirmar que el centro va PEGADO a su propia suscripción hay que leer el
# atributo completo y no buscar el valor suelto en la página.
CHECKBOX = re.compile(
    r'<input class="form-check-input subscription-check"'
    r'[^>]*?value="(?P<value>\d+)"'
    r'[^>]*?data-centro="(?P<centro>[^"]*)"',
    re.S,
)


class _PantallaDeFacturaBase(TestCase):
    """Cliente, servicios comerciales y usuario staff: el sustrato común."""

    @classmethod
    def setUpTestData(cls):
        # `CheckUserProfileMiddleware` exige nombre y apellido para poder
        # redirigir a la creación de perfil, así que un superuser sin ellos
        # nunca llega a la vista.
        cls.admin = User.objects.create_superuser(
            username='prefilladmin',
            email='prefill@example.com',
            password='pass',  # pragma: allowlist secret
            first_name='Admin',
            last_name='Prefill',
        )
        cls.customer = Customer.objects.create(
            client_type='juridica',
            user=User.objects.create_user(
                'prefillcust',
                'prefillcust@example.com',
                'pass',  # pragma: allowlist secret
                first_name='Cli',
                last_name='Prefill',
            ),
            company_name='Empresa Prefill',
            reeup='123.4.5678',
            nit='12345678901',
            account='9001000000000001',
            agency_bank='Banco Prefill',
        )
        cls.url_create = reverse('commercial:factura_create')
        cls.url_ajax = reverse('commercial:ajax_pending_subscriptions')


class ServiciosComercialesJsonTests(_PantallaDeFacturaBase):
    """El JSON que consume el `servicesMap` trae el centro ya resuelto."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.servicio_centro = Service.objects.create(
            user=cls.admin,
            title='Pronóstico diario',
            summary='Servicio con centro embebido en el código',
            service_type='commercial',
            service_category='pronostico',
            code='700501072507005',
            price=Decimal('45.00'),
        )
        cls.servicio_sin_centro = Service.objects.create(
            user=cls.admin,
            title='Servicio sin centro derivable',
            summary='Código corto: no hay prefijo del cual deducir un centro',
            service_type='commercial',
            service_category='agrometeo',
            code='123',
            price=Decimal('10.00'),
        )

    def _servicios_json(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url_create)
        datos = json.loads(response.context['commercial_services_json'])
        return {entrada['id']: entrada for entrada in datos}

    def test_el_json_incluye_el_centro_derivado_del_prefijo_del_codigo(self):
        servicios = self._servicios_json()

        entrada = servicios[self.servicio_centro.id]

        self.assertEqual(entrada['code'], '700501072507005')
        self.assertEqual(entrada['centro_de_costo'], '700.50107')

    def test_un_codigo_sin_centro_derivable_manda_none(self):
        """`None` y no `'None'`: el JS lo trata como ausencia y no inventa uno."""
        servicios = self._servicios_json()

        entrada = servicios[self.servicio_sin_centro.id]

        self.assertIsNone(entrada['centro_de_costo'])

    def test_el_json_sigue_trayendo_el_codigo_y_el_precio(self):
        """El centro es una clave más, no un reemplazo de lo que ya se usaba."""
        servicios = self._servicios_json()

        entrada = servicios[self.servicio_centro.id]

        self.assertEqual(entrada['code'], '700501072507005')
        self.assertEqual(entrada['price'], '45.00')
        self.assertEqual(entrada['service_category'], 'pronostico')


class AjaxPendingSubscriptionsCentroTests(_PantallaDeFacturaBase):
    """El endpoint del lote manda el centro resuelto, por suscripción."""

    def setUp(self):
        self.client.force_login(self.admin)
        self.service = Service.objects.create(
            user=self.admin,
            title='Pronóstico ajax',
            summary='Servicio para el endpoint',
            service_type='commercial',
            service_category='pronostico',
            code='700501072507005',
            price=Decimal('45.00'),
        )
        self.subscription = ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.service,
            quantity=10,
            payment_status='requested',
            start_date=timezone.now(),
        )

    def _centros_por_suscripcion(self, response):
        """`{pk de la suscripción: centro}` leído del atributo de cada casilla."""
        html = response.content.decode()
        return {match.group('value'): match.group('centro') for match in CHECKBOX.finditer(html)}

    def test_el_ajax_manda_el_centro_derivado_del_codigo_del_servicio(self):
        response = self.client.get(self.url_ajax, {'customer': self.customer.pk})

        self.assertContains(response, 'data-centro="700.50107"')

    def test_el_centro_va_por_suscripcion_y_no_por_cliente(self):
        """Dos servicios con prefijos distintos → dos centros distintos, cada uno
        en la casilla de su propia suscripción: el reparto se arma marcando."""
        otro = Service.objects.create(
            user=self.admin,
            title='Agrometeo ajax',
            summary='Otro servicio del mismo cliente',
            service_type='commercial',
            service_category='agrometeo',
            code='700502072507015',
            price=Decimal('80.00'),
        )
        segunda = ServiceSubscription.objects.create(
            customer=self.customer,
            service=otro,
            quantity=2,
            payment_status='requested',
            start_date=timezone.now(),
        )

        response = self.client.get(self.url_ajax, {'customer': self.customer.pk})

        self.assertEqual(
            self._centros_por_suscripcion(response),
            {
                str(self.subscription.pk): '700.50107',
                str(segunda.pk): '700.50207',
            },
        )

    def test_un_servicio_de_otro_tipo_sin_centro_no_aporta_centro(self):
        """Un servicio público con código no derivable no aporta centro: su
        casilla viaja con `data-centro` vacío y no se inventa ninguno."""
        publico = Service.objects.create(
            user=self.admin,
            title='Servicio público',
            summary='No es comercial y su código no trae prefijo',
            service_type='public',
            service_category='pronostico',
            code='ABC123',
            price=None,
        )
        pendiente = ServiceSubscription.objects.create(
            customer=self.customer,
            service=publico,
            quantity=1,
            payment_status='requested',
            start_date=timezone.now(),
        )

        response = self.client.get(self.url_ajax, {'customer': self.customer.pk})

        centros = self._centros_por_suscripcion(response)
        self.assertEqual(centros[str(pendiente.pk)], '')
        self.assertEqual(centros[str(self.subscription.pk)], '700.50107')


class EstructuraDeLaTarjetaDeImputacionTests(_PantallaDeFacturaBase):
    """La tarjeta de imputación es visible en el lote y en el manual.

    Mientras la tarjeta viviera dentro de `#manual-container`, el lote la
    ocultaba con `manualContainer.style.display = 'none'`: el reparto se
    precargaba y se enviaba a ciegas, sin que el operador pudiera repartir,
    que es exactamente lo único que quiere seguir haciendo a mano.
    """

    def setUp(self):
        self.client.force_login(self.admin)
        self.html = self.client.get(self.url_create).content.decode()

    def test_la_tarjeta_de_imputacion_queda_fuera_de_manual_container(self):
        """Cuenta la profundidad de `<div>` desde la apertura de
        `#manual-container` hasta el comienzo de la tarjeta: si la tarjeta
        quedara adentro, el contenedor manual todavía no habría cerrado."""
        inicio = self.html.index('<div id="manual-container"')
        # El ancla `id="imputacion-card"` cae dentro de la etiqueta de apertura
        # de la propia tarjeta, así que retrocede al `<div>` que la abre: de lo
        # contrario el recorrido contaría esa apertura y la profundidad nunca
        # sería 0 aunque la tarjeta esté donde tiene que estar.
        fin = self.html.rindex('<div', 0, self.html.index('id="imputacion-card"'))
        profundidad = 0
        for etiqueta in re.finditer(r'<div\b|</div>', self.html[inicio:fin]):
            profundidad += -1 if etiqueta.group() == '</div>' else 1
            self.assertGreaterEqual(profundidad, 0, 'un </div> de más dentro de #manual-container')

        self.assertEqual(
            profundidad,
            0,
            'la tarjeta de imputación sigue dentro de #manual-container',
        )

    def test_el_management_form_y_el_datalist_quedan_fuera_de_cost_container(self):
        """El JS borra el `innerHTML` de `#cost-container` en cada
        reconstrucción: si el management form o el datalist quedaran adentro,
        el POST perdería `TOTAL_FORMS` y el formset se rompería."""
        indice_management = self.html.index('id_cost_allocations-TOTAL_FORMS')
        indice_datalist = self.html.index('id="centros-de-costo"')
        indice_cost_container = self.html.index('id="cost-container"')

        self.assertLess(indice_management, indice_cost_container)
        self.assertLess(indice_datalist, indice_cost_container)

    def test_la_tarjeta_de_imputacion_tiene_su_id_estable(self):
        self.assertIn('id="imputacion-card"', self.html)


class DerivacionDeCentrosEnElNavegadorTests(TestCase):
    """El reparto se deriva en el navegador, con el centro resuelto por el servidor.

    Sin navegador no se puede ejercitar un handler, así que éstas son pruebas
    sobre la **fuente** del JS inline y no sobre el HTML renderizado: ahí están
    los códigos de los servicios que JSON.parse incrusta en la página, y un
    `assertNotIn` sobre el render acusaría a los datos de ser la regla. Cubren
    lo que sí se puede romper sin que ningún test de vistas lo vea —una regla
    del prefijo duplicada, un centro que el template no copia, un punto de
    enganche desconectado.

    Dicho sin rodeos: **son contratos de fuente, no pruebas de comportamiento**.
    Este proyecto no tiene runner de JS (sin npm, sin jsdom, sin
    playwright/selenium), así que el reparto real en el navegador no se puede
    ejercitar. Se afirma que ciertos patrones están en la fuente; que esos
    patrones hagan lo correcto al ejecutarse queda como limitación declarada.
    """

    def setUp(self):
        plantilla = (
            settings.BASE_DIR
            / 'apps'
            / 'commercial'
            / 'templates'
            / 'pages'
            / 'commercial'
            / 'invoice'
            / 'create.html'
        )
        self.js = plantilla.read_text(encoding='utf-8')

    def bloque_desde(self, desde, hasta):
        inicio = self.js.index(desde)
        return self.js[inicio : self.js.index(hasta, inicio)]

    def test_el_checkbox_del_lote_que_reconstruye_el_js_conserva_el_centro(self):
        """`loadPendingSubscriptions` reescribe los checkboxes con su propio
        template literal: si no copia `data-centro`, cada marca posterior
        deriva un reparto vacío y el lote vuelve a ser imputación a ciegas."""
        self.assertIn('data-centro="${escapeHtml(cb.dataset.centro || \'\')}"', self.js)

    def test_el_mapa_de_servicios_del_js_iza_el_centro_del_json(self):
        self.assertIn('centro_de_costo: s.centro_de_costo', self.js)
        self.assertIn('data.centro_de_costo', self.js)

    def test_la_regla_del_prefijo_no_vuelve_a_vivir_en_el_js(self):
        """Si el navegador volviera a partir el código, la regla existiría en
        dos archivos y las dos podrían divergir sin que ningún test lo vea."""
        self.assertNotIn('centroDeCostoDeCodigo', self.js)
        self.assertNotIn('700501072507005', self.js)
        self.assertNotRegex(self.js, r'\.substring\(0,\s*6\)')
        self.assertNotRegex(self.js, r'\.slice\(0,\s*6\)')

    def test_los_puntos_de_enganche_de_la_derivacion_siguen_cableados(self):
        """Cada entrada que cambia qué se está facturando vuelve a derivar:
        cambio a manual, carga del lote, cambio de servicio, alta de fila,
        baja de fila y marcar una suscripción del lote."""
        puntos = [
            (
                'cambio a facturación manual',
                'function switchToManualInvoice',
                'function mostrarFacturacionManual',
            ),
            (
                'carga de la lista del lote',
                'function loadPendingSubscriptions',
                '/* ===== Imputación a centros de costo en vivo',
            ),
            (
                'cambio de servicio en una línea',
                'function updateRowFromService',
                'function bindRowEvents',
            ),
            (
                'baja de una fila',
                "removeBtn.addEventListener('click'",
                "document.querySelectorAll('.item-row')",
            ),
            (
                'alta de una fila',
                "getElementById('add-item')",
                '/* Imputación a centros de costo: mismo patrón',
            ),
            (
                'marcar una suscripción del lote',
                "groupedContainer.addEventListener('change'",
                'function updateRowFromService',
            ),
        ]
        for nombre, desde, hasta in puntos:
            with self.subTest(punto=nombre):
                self.assertIn(
                    'prefijarImputacion()',
                    self.bloque_desde(desde, hasta),
                    f'{nombre} no vuelve a derivar el reparto',
                )

    def test_la_derivacion_tiene_sus_dos_guardas(self):
        """Sin selección no se toca nada, y con los centros derivados ya en
        pantalla y ninguno huérfano tampoco se reconstruye: las dos frenan que
        la derivación pise al operador. La segunda se decide con `faltan` y
        `sobran` —contra el último conjunto derivado— y no comparando la
        pantalla contra lo derivado, porque una fila manual nunca está en el
        conjunto derivado y esa comparación la descartaría siempre."""
        self.assertIn('derivados.length === 0', self.js)
        self.assertIn('faltan.length === 0 && sobran.length === 0', self.js)

    def test_el_ultimo_conjunto_derivado_se_recuerda_y_se_actualiza_al_decidir(self):
        """La guarda no puede comparar contra la pantalla: recuerda aparte el
        último conjunto DERIVADO y decide con él, y lo actualiza después de
        cada decisión —haya reconstruido o no—. Contrato de fuente: se afirma
        el patrón (declaración más las dos actualizaciones), no el
        comportamiento."""
        self.assertIn('let ultimosDerivados = [];', self.js)
        bloque = self.bloque_desde('function prefijarImputacion', '// Delegado, no directo')
        self.assertEqual(
            bloque.count('ultimosDerivados = derivados;'),
            2,
            'el estado se actualiza en los dos caminos: sin reconstruir y tras reconstruir',
        )

    def test_las_filas_manuales_se_filtran_por_el_ultimo_conjunto_derivado(self):
        """Antes de reconstruir, las filas del operador son las que están en
        pantalla y NO venían en el último conjunto derivado. Si se filtraran
        por el conjunto derivado ACTUAL, cada fila agregada a mano se
        descartaría, porque un centro manual nunca está en lo que se deriva."""
        bloque = self.bloque_desde('function prefijarImputacion', '// Delegado, no directo')
        self.assertRegex(
            bloque,
            r'manuales\s*=\s*enPantalla\.filter\(function\s*\(centro\)\s*\{\s*'
            r'return\s+ultimosDerivados\.indexOf\(centro\)\s*===\s*-1;',
        )
        self.assertNotRegex(
            bloque,
            r'manuales\s*=\s*enPantalla\.filter\(function\s*\(centro\)\s*\{\s*'
            r'return\s+derivados\.indexOf\(',
        )
