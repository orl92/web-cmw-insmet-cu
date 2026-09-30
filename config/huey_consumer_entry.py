"""Entrada del consumer de Huey: `huey_consumer` apunta acá, no a `config.huey`.

El paso de `django.setup()` no es opcional ni decorativo. El binario
`huey_consumer` importa el módulo que se le pasa y toma de ahí la instancia, pero
no conoce Django: con solo `DJANGO_SETTINGS_MODULE` exportado (que es lo que hacía
antes) los decoradores `@huey.task()` de `apps/core/tasks.py` nunca se ejecutan, el
TaskRegistry queda vacío, y cada dequeue revienta con
`HueyException: <tarea> not found in TaskRegistry`. El worker queda "vivo" para
siempre, sin procesar una sola tarea, y el único síntoma es un ciclo de errores en
el log.

Se llama `config.huey_consumer_entry` y no `config.huey` a propósito: el módulo de
la instancia se importa desde `apps.core.tasks`, que corre durante `django.setup()`,
y no puede llamar a `setup()` en su propia importación sin riskear
`AppRegistryNotReady` en el proceso web.
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django  # noqa: E402

django.setup()

from config.huey import huey  # noqa: E402, F401  (re-export: es lo que lee el CLI)

__all__ = ['huey']
