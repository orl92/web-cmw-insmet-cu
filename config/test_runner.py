import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.test.runner import DiscoverRunner
from huey.storage import MemoryStorage

from config.huey import huey


class IsolatedMediaRunner(DiscoverRunner):
    """Aísla los dos estados en disco que una corrida de tests puede tocar.

    1. `MEDIA_ROOT`: se redirige a un tempdir que se borra al terminar, así que
       los `FileField`/`ImageField` y los PDF que generan los tests no caen en el
       `media/` real.

    2. La cola de Huey: `config.huey.huey` es un `SqliteHuey` sobre
       `BASE_DIR/huey.db` y el test runner aísla la base de datos, NO ese archivo.
       Sin este aislamiento los tests que encolan —o que reencolan al reintentar—
       dejan tareas con `site_url='http://testserver/'` en la cola de desarrollo
       y `run_huey.sh` se come un traceback por cada una. Durante la corrida el
       storage es un `MemoryStorage` y se restaura al terminar.

       Hay que cambiar `storage` Y `storage_class`: el setter de `huey.immediate`
       recrea el storage con `create_storage()` cada vez que cambia, así que un
       test que hace `huey.immediate = True` y vuelve al valor anterior
       (los de monitoreo de tareas lo hacen) deja un `SqliteStorage` nuevo
       apuntando a `huey.db` y a partir de ahí la suite escribe en la cola real.

    Importar `config.huey` acá no rompe el orden de imports: este runner se
    construye y se ejecuta después de `django.setup()`, así que `config.settings`
    ya está configurado; de hecho `config.huey` ya fue importado por
    `apps.core.apps.ready()`. Ese import crea `huey.db` al construirse el
    `SqliteHuey`, o sea en `django.setup()`, antes de que corra este runner: el
    archivo existe siempre, aunque no haya nada encolado. Eso no es basura de los
    tests (lo crea cualquier comando de `manage.py`) y por eso el aislamiento no
    lo borra: borrarlo con un `run_huey.sh` vivo dejaría al consumer escribiendo
    sobre un inode desaparecido, encolando para siempre sin que nadie lo lea.
    """

    def setup_test_environment(self, **kwargs):
        self._tmp_media_root = Path(tempfile.mkdtemp(prefix='opencode_test_media_'))
        self._original_media_root = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = self._tmp_media_root
        self._original_huey_storage = huey.storage
        self._original_huey_storage_class = huey.storage_class
        huey.storage_class = MemoryStorage
        huey.storage = huey.create_storage()
        super().setup_test_environment(**kwargs)

    def teardown_test_environment(self, **kwargs):
        super().teardown_test_environment(**kwargs)
        settings.MEDIA_ROOT = self._original_media_root
        huey.storage = self._original_huey_storage
        huey.storage_class = self._original_huey_storage_class
        shutil.rmtree(self._tmp_media_root, ignore_errors=True)
