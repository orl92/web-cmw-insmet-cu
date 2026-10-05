"""`FileObs` tiene que escribir adentro de `MEDIA_ROOT`, no en `./media/`.

Los directorios estaban hardcodeados como `'./media/obs'` y `'./media/temp'`,
relativos al directorio desde el que se arranca el proceso. Eso rompía dos cosas:
con el `MEDIA_ROOT` que redirige el test runner, los tests se escapaban del
aislamiento y dejaban SYNOP en el `media/` real; y en producción, si el servicio
se arrancara desde otro cwd, los archivos caían en un lugar inesperado.

Se derivan de `settings.MEDIA_ROOT`, igual que el autogenerador local del API
(`apps/api/views.py`), que ya lo hacía bien.
"""

from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, override_settings

from apps.api.data.FileObs import FileObs


def dentro_de_media_root(ruta):
    """True si `ruta` está adentro del MEDIA_ROOT activo (no sólo con prefijo)."""
    raiz = Path(settings.MEDIA_ROOT).resolve()
    return Path(ruta).resolve().is_relative_to(raiz)


class RutasDeFileObsTests(SimpleTestCase):
    def test_los_directorios_caen_dentro_de_media_root(self):
        """Con el runner activo, `FileObs` no puede tocar el `media/` real."""
        obs = FileObs()
        for nombre, ruta in (('FINAL_DIR', obs.FINAL_DIR), ('TEMP_DIR', obs.TEMP_DIR)):
            with self.subTest(directorio=nombre):
                self.assertTrue(
                    dentro_de_media_root(ruta),
                    f'{nombre}={ruta} está fuera de MEDIA_ROOT={settings.MEDIA_ROOT}',
                )

    def test_los_directorios_siguen_a_media_root(self):
        """La prueba de que se DERIVAN de MEDIA_ROOT y no de una ruta fija: se
        cambia el setting y las rutas se mueven con él."""
        obs = FileObs()
        with override_settings(MEDIA_ROOT=Path(settings.BASE_DIR) / 'media'):
            self.assertEqual(Path(FileObs().FINAL_DIR), Path(settings.BASE_DIR) / 'media' / 'obs')
            self.assertEqual(Path(FileObs().TEMP_DIR), Path(settings.BASE_DIR) / 'media' / 'temp')
        # Fuera del override vuelven a su valor: no se cacheó nada en el atributo.
        self.assertTrue(dentro_de_media_root(obs.FINAL_DIR))

    def test_las_rutas_son_str_para_el_resto_del_modulo(self):
        """`os.path.join`, `os.makedirs` y el comando de lftp las tratan como
        texto: cambiar el tipo rompería el downloader en silencio."""
        obs = FileObs()
        self.assertIsInstance(obs.FINAL_DIR, str)
        self.assertIsInstance(obs.TEMP_DIR, str)

    def test_no_deja_rutas_relativas_al_cwd(self):
        """La regresión concreta: nada de './media/...' ni rutas relativas."""
        obs = FileObs()
        for nombre, ruta in (('FINAL_DIR', obs.FINAL_DIR), ('TEMP_DIR', obs.TEMP_DIR)):
            with self.subTest(directorio=nombre):
                self.assertTrue(Path(ruta).is_absolute(), f'{nombre}={ruta} es relativa')
