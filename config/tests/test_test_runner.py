"""El runner de tests tiene que dejar la máquina como la encontró.

`config.test_runner.IsolatedMediaRunner` aísla las dos escrituras que una corrida
puede hacer fuera de la base de datos de test: el `MEDIA_ROOT` real y el archivo
de la cola de Huey (`huey.db`). Estos tests fijan ese contrato como aserción,
porque la alternativa —creer que los tests no ensucian— es exactamente lo que
dejó 80 tareas con `site_url='http://testserver/'` en la cola de desarrollo.

Estos tests corren DENTRO de la suite, o sea con el runner ya activo: verifican
el efecto observable durante la corrida. Para el efecto sobre el disco, el chequeo
definitivo es el antes/después del archivo en la verificación manual: la cola tiene
que seguir existiendo (la crea `django.setup()`, no los tests) y con las mismas
filas que tenía, ni una más.
"""

import sqlite3
from contextlib import closing
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase
from huey.storage import MemoryStorage

from config.huey import HUEY_DB_PATH, huey


def tareas_en_la_cola_en_disco():
    """Cuántas tareas tiene el archivo de la cola real de este proyecto.

    Devuelve 0 si el archivo no existe. Durante los tests lo normal es que exista
    (lo crea `django.setup()` al construir el `SqliteHuey`) y conserve las tareas
    que el desarrollador tenía: lo que no puede pasar es que los tests le sumen
    alguna.
    """
    path = Path(HUEY_DB_PATH)
    if not path.exists():
        return 0
    try:
        with closing(sqlite3.connect(f'file:{path}?mode=ro', uri=True)) as conn:
            return conn.execute('SELECT COUNT(*) FROM task').fetchone()[0]
    except sqlite3.Error:
        return -1  # ilegible: no se puede afirmar nada, el test debe fallar


class MediaRootAisladoTests(SimpleTestCase):
    """`MEDIA_ROOT` apunta al tempdir del runner, no al `media/` del repo.

    También fijan que `TEST_RUNNER` sea este: correrlos con el runner default
    no daría ni `MemoryStorage` ni tempdir, y pasarían mintiendo.
    """

    def test_el_runner_es_el_registrado_en_settings(self):
        self.assertEqual(settings.TEST_RUNNER, 'config.test_runner.IsolatedMediaRunner')

    def test_media_root_no_es_el_del_repo(self):
        media_root = Path(settings.MEDIA_ROOT)
        self.assertNotEqual(media_root, Path(settings.BASE_DIR) / 'media')
        self.assertTrue(media_root.is_dir(), f'{media_root} no existe')


class ColaDeHueyAisladaTests(TestCase):
    """Durante la corrida la cola es en memoria: nada llega a `huey.db`.

    `TestCase` y no `SimpleTestCase` porque encolar dispara el signal
    `SIGNAL_ENQUEUED`, que escribe el `TaskExecutionLog`: es el camino real que
    recorren los tests que contaminaban la cola.
    """

    def test_el_storage_no_es_de_archivo(self):
        self.assertIsInstance(huey.storage, MemoryStorage)
        # Un storage de archivo (SqliteStorage) expone `filename`; el de memoria
        # no. Es el detalle que distingue "encoló en memoria" de "encoló en la
        # cola real": ambos son storage válido para huey.
        self.assertFalse(hasattr(huey.storage, 'filename'))

    def test_toggle_de_immediate_no_revierte_el_aislamiento(self):
        """La regresión que cuesta entender si no se lee el código de huey.

        El setter de `huey.immediate` RECREA el storage (`create_storage()`) cada
        vez que el valor cambia, con `huey.storage_class`. Los tests de monitoreo
        de tareas hacen `immediate = True` y vuelven al valor anterior: con sólo
        cambiar `huey.storage` a un `MemoryStorage`, ese `False` final instalaba un
        `SqliteStorage` nuevo sobre `huey.db` y la suite seguía escribiendo en la
        cola del desarrollador a partir de ahí.
        """
        original = huey.immediate
        try:
            huey.immediate = True
            huey.immediate = original
        finally:
            huey.immediate = original

        self.assertIsInstance(huey.storage, MemoryStorage)
        self.assertIs(huey.storage_class, MemoryStorage)

    def test_enqueue_no_toca_el_archivo_de_la_cola(self):
        """El invariante real, no el tipo: encolar una tarea no suma una fila.

        Es el bug que se quiere cerrar. Los tests reintentan (retries=3) y
        reencolan desde el dashboard, así que cada falla dejaba una tarea en la
        cola del desarrollador y `run_huey.sh` la consumía con un traceback.
        """

        @huey.task()
        def _tarea_que_no_debe_persistir():
            return 'nada'

        antes = tareas_en_la_cola_en_disco()
        pendientes_antes = huey.pending_count()

        _tarea_que_no_debe_persistir()

        # La tarea se encoló de verdad...
        self.assertEqual(huey.pending_count(), pendientes_antes + 1)
        # ...pero no llegó al archivo.
        self.assertEqual(tareas_en_la_cola_en_disco(), antes)
