"""Las URLs del geojson del mapa tienen que ser absolutas.

`static/dist/js/map_station.js` cargaba el geojson con rutas relativas
("static/dist/json/..."), que el navegador resuelve contra el path de la pagina.
En `/home/` eso terminaba en `/home/static/dist/json/contry_data.json`, un 404
que Django responde en HTML: `am5.net.load` lo rechaza y el mapa no se dibuja
nada, sin error visible en la consola de Django. El `type: "text/html"` del XHR
era la unica pista.

Por eso el template pasa las URLs con `{% static %}` en data-* y estos tests
verifican que sigan siendo absolutas: el mismo bug volvería en silencio.
"""

import re

from django.test import TestCase
from django.urls import reverse

MAPA_JS = 'dist/js/map_station.js'
DATA_ATTRS = ('data-geo-countries-url', 'data-geo-camaguey-url')


class GeojsonDelMapaEsAbsolutoTests(TestCase):
    def setUp(self):
        self.html = self.client.get(reverse('home:index')).content.decode()

    def test_el_template_pasa_las_urls_del_geojson(self):
        for attr in DATA_ATTRS:
            with self.subTest(attr=attr):
                self.assertIn(attr, self.html, f'el script del mapa no declara {attr}')

    def test_las_urls_del_geojson_no_son_relativas(self):
        """El bug: una ruta relativa se resuelve contra el path de la pagina."""
        for attr in DATA_ATTRS:
            with self.subTest(attr=attr):
                url = re.search(rf'{attr}="([^"]+)"', self.html).group(1)
                self.assertTrue(url.startswith('/'), f'{attr}="{url}" no es absoluta')
                self.assertNotIn('/home/', url, f'{attr}="{url}" arrastra el path de la pagina')

    def test_el_js_no_carga_el_geojson_con_ruta_relativa(self):
        """Guarda el JS, no solo el template: el fallback tambien debe ser absoluto."""
        from django.contrib.staticfiles import finders

        ruta = finders.find(MAPA_JS)
        self.assertIsNotNone(ruta, f'{MAPA_JS} no se encuentra en los staticfiles')
        with open(ruta) as fh:
            js = fh.read()

        for carga in re.findall(r'am5\.net\.load\(([^,]+),', js):
            with self.subTest(carga=carga):
                self.assertNotIn('"', carga, f'am5.net.load({carga}) usa una ruta relativa')
        for fallback in re.findall(r"getAttribute\('data-geo-[a-z-]+-url'\) \|\| '([^']+)'", js):
            with self.subTest(fallback=fallback):
                self.assertTrue(fallback.startswith('/'), f'fallback "{fallback}" no es absoluto')
