"""El picker de fecha de una línea agregada con "Añadir servicio" se inicializa.

En el formulario de factura manual la primera fila trae su calendario, pero una
fila clonada con el botón "Añadir servicio" no: `tempus-init.js` inicializa los
`[data-tempus]` UNA sola vez, dentro de `DOMContentLoaded`, y no observa los
nodos que aparecen después. `proposeLineStartDate` escribía la fecha en el input
sin construir el picker, así que en la fila nueva el calendario no abría.

El arreglo tiene dos piezas y este módulo fija las dos como contratos:

1. `tempus-init.js` expone su inicializador local como `window.initPicker`, para
   que un script de plantilla pueda construir el picker de un nodo nuevo. La
   guarda anti-doble-init que ya tenía `initPicker` hace inocua una llamada
   repetida.
2. El handler de `#add-item` de `create.html` inicializa los `[data-tempus]` de
   la fila clonada con `window.initPicker`, detrás de una guarda de tipo, y
   DESPUÉS de `proposeLineStartDate`: TD6 lee el valor del input al construir su
   widget, así que inicializar antes dejaría el picker abriendo sin fecha.

EXCEPCIÓN DELIBERADA A LA POLÍTICA TEST-FIRST (RED no observable): este proyecto
no tiene runner de JavaScript (sin npm, sin bundlers, sin jsdom ni
playwright/selenium). Un RED real sobre el comportamiento del calendario no se
puede ejercitar acá. En su lugar se fijan **contratos de fuente**: se afirma que
los patrones de cableado están en los archivos. Que al ejecutarse hagan lo
correcto queda como limitación declarada.
"""

from django.conf import settings
from django.test import SimpleTestCase

TEMPUS_INIT = settings.BASE_DIR / 'static' / 'dist' / 'js' / 'tempus-init.js'
CREATE_HTML = (
    settings.BASE_DIR
    / 'apps'
    / 'commercial'
    / 'templates'
    / 'pages'
    / 'commercial'
    / 'invoice'
    / 'create.html'
)

# El handler de alta va desde su registro hasta el bloque siguiente; entre esos
# dos delimitadores está todo lo que hace el botón, y nada más.
ALTA_DESDE = "getElementById('add-item')"
ALTA_HASTA = '/* Imputación a centros de costo: mismo patrón'


class _ContratosDeFuente(SimpleTestCase):
    """Lee los archivos como texto: no hay navegador que ejecute el JS."""

    def setUp(self):
        self.tempus = TEMPUS_INIT.read_text(encoding='utf-8')
        self.html = CREATE_HTML.read_text(encoding='utf-8')

    def bloque_del_alta(self):
        inicio = self.html.index(ALTA_DESDE)
        return self.html[inicio : self.html.index(ALTA_HASTA, inicio)]


class InitPickerExpuestoTests(_ContratosDeFuente):
    """El inicializador local sale del closure como global."""

    def test_tempus_init_expone_el_inicializador_como_global(self):
        """Sin el global, ningún script de plantilla puede inicializar un nodo nuevo."""
        self.assertIn('function initPicker(input)', self.tempus)
        self.assertIn('window.initPicker = initPicker;', self.tempus)

    def test_la_guarda_anti_doble_inicio_sigue_en_su_lugar(self):
        """Es lo que vuelve inocua una llamada repetida desde el alta de fila."""
        self.assertIn(
            'window.tempusDominus._instances[input.id]',
            self.tempus,
        )


class AltaDeFilaInicializaElPickerTests(_ContratosDeFuente):
    """La fila clonada construye el picker de su propia fecha."""

    def test_el_alta_de_fila_inicializa_los_pickers_de_la_fila_nueva(self):
        bloque = self.bloque_del_alta()

        self.assertIn("typeof window.initPicker === 'function'", bloque)
        self.assertIn('window.initPicker(input)', bloque)

    def test_la_llamada_esta_detras_de_la_guarda_de_tipo(self):
        """Los scripts de plantilla pueden correr antes que tempus-init.js: si el
        global no está, el alta no debe romper ni lanzar excepción."""
        bloque = self.bloque_del_alta()

        self.assertLess(
            bloque.index("typeof window.initPicker === 'function'"),
            bloque.index('window.initPicker(input)'),
            'la guarda de tipo tiene que envolver la llamada',
        )

    def test_la_fecha_se_propone_antes_de_inicializar_el_picker(self):
        """TD6 lee el input al construir el widget: inicializar antes abriría sin
        fecha. El orden appendChild → proposeLineStartDate → picker es el contrato."""
        bloque = self.bloque_del_alta()

        self.assertLess(
            bloque.index('container.appendChild(newRow)'),
            bloque.index('proposeLineStartDate(newRow)'),
        )
        self.assertLess(
            bloque.index('proposeLineStartDate(newRow)'),
            bloque.index('window.initPicker(input)'),
            'el picker se inicializa después de escribir la fecha',
        )
