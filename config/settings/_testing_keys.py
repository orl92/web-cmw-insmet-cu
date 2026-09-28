"""Par de claves determinista del perfil `testing`.

Vive en su propio módulo, y no dentro de `testing.py`, porque hay DOS caminos
que necesitan inyectarlo y antes de importar `base`:

- `config.settings` (el dispatcher), que tiene que saber que el perfil es
  `testing` ANTES de importar nada, y por lo tanto antes de importar `base`.
- `config.settings.testing` importado directo
  (`DJANGO_SETTINGS_MODULE=config.settings.testing`), que es lo que promete la
  docstring del dispatcher.

Un dueño, dos llamadores. Duplicar el par en los dos sitios haría que un cambio
en uno de ellos dejara al otro usando material de clave viejo.
"""

import base64
import hashlib
import os

from cryptography.fernet import Fernet

# Clave pública y de prueba: no protege nada y no debe usarse fuera de la suite.

# DERIVADA, no escrita. Fernet exige 32 bytes en base64 urlsafe, y poner esa
# cadena literal en el repo la convierte en un string de alta entropía que
# `detect-secrets` marca como secreto —con razón, aparenta serlo—. `sha256` de
# una constante pública da exactamente esos 32 bytes, siempre iguales, y no hay
# nada que alguien pueda intentar usar.
_FERNET_KEY = base64.urlsafe_b64encode(hashlib.sha256(b'webcmp-testing-key-pair').digest())

# 63 caracteres y 29 distintos: cumple el criterio de `security.W009` (>=50
# caracteres, >=5 distintos, sin prefijo `django-insecure-`), que es lo que
# evalúa el job `deploy-check` de CI sobre este mismo perfil.
_PLAIN_SECRET = b'testing-only-secret-key-not-a-real-secret-0123456789-abcdefghij'


def inject_testing_key_pair() -> None:
    """Pone el par en el entorno si no hay otro. Idempotente y no sobreescribe.

    `setdefault` y no asignaciones: si el operador exporta un material real para
    correr la suite contra algo parecido a producción, esta función no lo pisa.
    La suite puede correr con material real; lo que no puede es quedarse sin
    ninguno.
    """
    os.environ.setdefault('ENCRYPTION_KEY', _FERNET_KEY.decode())
    os.environ.setdefault('SECRET_KEY', Fernet(_FERNET_KEY).encrypt(_PLAIN_SECRET).decode())
