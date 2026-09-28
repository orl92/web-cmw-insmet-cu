"""Punto de entrada de la configuración: selecciona el perfil y lo reexporta.

RESTRICCIÓN DURA (no negociable): el perfil lo eligen las MISMAS variables de
entorno que leía el monolito `config/settings.py`, con la MISMA precedencia:

    IS_PRODUCTION = 'PRODUCTION' in os.environ
    DEBUG = os.getenv('DEBUG', 'False') == 'True'

`gunicorn.sh` no exporta `PRODUCTION` (la define el `supervisord.conf` del
servidor de deploy, fuera del repo). Si esta selección usara otra variable, un
supervisor que no la exportara arrancaría producción con el perfil equivocado:
un outage silencioso. Por eso la tabla de verdad se preserva por construcción:

    PRODUCTION en el entorno        ->  production
    sin PRODUCTION, DEBUG == True   ->  dev
    sin PRODUCTION, DEBUG != True   ->  testing

`PRODUCTION` gana sobre `DEBUG`, como antes. `load_dotenv()` corre dentro de
`base`, que se importa antes de leer las banderas, así que `.env` participa en la
decisión igual que participaba en el monolito.

Los perfiles también son importables por su cuenta
(`DJANGO_SETTINGS_MODULE=config.settings.production`): cada uno hace su propio
`from .base import *`.
"""

# Los settings del perfil llegan por `import *` a propósito: `config.settings` es
# un módulo de settings completo, no un selector.
# ruff: noqa: F405
import os

from . import base as _base
from .base import _CONTENT_SECURITY_POLICY_DIRECTIVES  # noqa: F401  (`import *` no lo exporta)

if 'PRODUCTION' in os.environ:
    from .production import *  # noqa: F403
elif _base.DEBUG:
    from .dev import *  # noqa: F403
else:
    from .testing import *  # noqa: F403


def get_database_config():
    """Envoltura de `base.get_database_config()`.

    Antes de la partición el helper leía `DEBUG` e `IS_PRODUCTION` del propio
    módulo `config.settings`, y los tests los parchean con
    `mock.patch.object(config.settings, 'DEBUG', ...)`. La envoltura lee los
    mismos dos nombres en ESTE módulo y delega la construcción en `base`, de
    modo que ese contrato se conserva tal cual.
    """
    return _base.get_database_config(is_production=IS_PRODUCTION, prefer_sqlite=DEBUG)


def load_tests(loader, tests, pattern):
    """Evita que `unittest` importe este paquete buscando tests dentro.

    Motivo: el descubrimiento trata todo módulo `test*.py` de un paquete como
    módulo de tests y lo IMPORTA. `config/settings/testing.py` es un perfil de
    settings, no un test: importarlo ejecuta su validación estricta de secretos
    y de base de datos, y lanza `ImproperlyConfigured` si el entorno no coincide
    con ese perfil. Con un `.env` local que pone `DEBUG=True` (perfil `dev`) y
    un bloque `DB_*` incompleto, `manage.py test` fallaba durante el
    descubrimiento con un error que nada tenía que ver con los tests.

    El protocolo `load_tests` de `unittest` hace que el descubrimiento use lo que
    se devuelve aquí y NO entre en `config/settings/`. Este paquete no contiene
    ningún test, así que se devuelve la suite vacía tal cual.
    """
    return tests
