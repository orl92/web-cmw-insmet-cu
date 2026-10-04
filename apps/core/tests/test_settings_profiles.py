"""Truth table de los perfiles de `config.settings` (odd/tasks/split-config-settings.md).

Cada perfil se carga con `importlib` bajo un entorno controlado —`dotenv`
neutralizado y `os.environ` limpio— así que la tabla se verifica en los estados
canónicos, no en el estado accidental que produce un `.env` local.

    PRODUCTION en el entorno        ->  production
    sin PRODUCTION, DEBUG == True   ->  dev
    sin PRODUCTION, DEBUG != True   ->  testing

Estos tests corren bajo `config.settings`, el perfil que el dispatcher eligió al
arrancar el test runner; por eso cargan los perfiles por su cuenta en vez de
mirar `django.conf.settings`.
"""

import importlib
import os
import warnings
from unittest import mock

from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.settings import base

DEBUG_TOOLBAR_APP = 'debug_toolbar'
DEBUG_TOOLBAR_MIDDLEWARE = 'debug_toolbar.middleware.DebugToolbarMiddleware'
STATIC_FILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
MANIFEST_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
SQLITE_ENGINE = 'django.db.backends.sqlite3'
# Literal, no el `base.console_email_backend`: el test tiene que fijar la cadena
# exacta que el perfil de producción rechaza, no seguir a la constante.
CONSOLE_EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DJANGO_SMTP_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
CUSTOM_EMAIL_BACKEND = 'config.custom_email_backend.CustomSTARTTLSBackend'

# El bloque de cookies seguras del monolito (`if not DEBUG:`) setting por setting.
SECURE_COOKIE_VALUES = {
    'SECURE_SSL_REDIRECT': False,
    'SECURE_PROXY_SSL_HEADER': ('HTTP_X_FORWARDED_PROTO', 'https'),
    'SECURE_CONTENT_TYPE_NOSNIFF': True,
    'SESSION_COOKIE_SECURE': True,
    'CSRF_COOKIE_SECURE': True,
    'SECURE_HSTS_SECONDS': 31536000,
    'SECURE_HSTS_INCLUDE_SUBDOMAINS': True,
    'SECURE_HSTS_PRELOAD': True,
    'SECURE_REFERRER_POLICY': 'same-origin',
    'SECURE_CROSS_ORIGIN_OPENER_POLICY': 'same-origin',
}


def load_profile(module_path, env):
    """Carga `module_path` con `env` como único entorno.

    Recarga `base` primero: es el que lee `DEBUG`/`IS_PRODUCTION` y el que
    ejecuta `load_dotenv()` (neutralizado acá para que `.env` no decida por
    nosotros). No toca el objeto `django.conf.settings`, que ya copió sus valores.
    """
    with (
        mock.patch.dict(os.environ, env, clear=True),
        mock.patch('dotenv.load_dotenv'),
        warnings.catch_warnings(),
    ):
        # Los perfiles que se cargan SIN par de claves recorren el fallback a
        # clave efímera, y ese camino ahora avisa (`EphemeralSecretKeyWarning`).
        # Sin este ignore, cada `reload` de `base` escupe 6 líneas de warning a la
        # salida del runner y termina tapando los avisos que sí importan.
        # El filtro va por MENSAJE y no por la clase a propósito: `reload(base)`
        # crea un `EphemeralSecretKeyWarning` nuevo (identidad distinta) en cada
        # pasada, así que un filtro por categoría quedaría viejo al segundo reload.
        # Los tests que sí necesitan observar el aviso (EphemeralSecretKeyFallbackTests)
        # no pasan por acá: usan su propio helper.
        warnings.filterwarnings('ignore', message='^SECRET_KEY ausente', category=UserWarning)
        importlib.reload(base)
        return importlib.reload(importlib.import_module(module_path))


def secret_env():
    """Par `SECRET_KEY`/`ENCRYPTION_KEY` válido, como el que genera `generate_env`.

    Sin esto el perfil de producción hace fail-fast en el import y no hay forma
    de examinar el resto de sus decisiones.
    """
    key = Fernet.generate_key()
    return {
        'SECRET_KEY': Fernet(key).encrypt(b'secret-key-de-prueba').decode(),
        'ENCRYPTION_KEY': key.decode(),
    }


class SecureCookieAssertionsMixin:
    """El bloque de cookies seguras: presente en testing/producción, ausente en dev."""

    def assert_secure_cookies(self, module):
        for name, value in SECURE_COOKIE_VALUES.items():
            self.assertEqual(
                getattr(module, name), value, f'{module.__name__}.{name} no coincide con la tabla'
            )

    def assert_no_secure_cookies(self, module):
        # Ausentes, no "con el default de Django": el monolito no los definía.
        for name in SECURE_COOKIE_VALUES:
            self.assertNotIn(name, vars(module), f'{module.__name__} no debe definir {name}')


class DebugToolbarAssertionsMixin:
    def assert_debug_toolbar(self, module):
        self.assertIs(module.DEBUG_TOOLBAR_ENABLED, True)
        self.assertIn(DEBUG_TOOLBAR_APP, module.INSTALLED_APPS)
        self.assertEqual(module.INTERNAL_IPS, ['127.0.0.1', '::1'])
        self.assertEqual(module.DEBUG_TOOLBAR_CONFIG, {'IS_RUNNING_TESTS': False})
        self.assertEqual(module.MIDDLEWARE[-1], DEBUG_TOOLBAR_MIDDLEWARE)

    def assert_no_debug_toolbar(self, module):
        self.assertIs(module.DEBUG_TOOLBAR_ENABLED, False)
        self.assertNotIn(DEBUG_TOOLBAR_APP, module.INSTALLED_APPS)
        self.assertNotIn(DEBUG_TOOLBAR_MIDDLEWARE, module.MIDDLEWARE)
        # El toolbar desaparecía con sus dos settings, no con un default.
        self.assertNotIn('DEBUG_TOOLBAR_CONFIG', vars(module))
        self.assertNotIn('INTERNAL_IPS', vars(module))


class DevProfileTests(SecureCookieAssertionsMixin, DebugToolbarAssertionsMixin, SimpleTestCase):
    """`DEBUG=True`: sqlite, toolbar, sin cookies seguras, sin WhiteNoise."""

    def setUp(self):
        self.module = load_profile(
            'config.settings.dev',
            # DB_ENGINE presente a propósito: sqlite tiene que ganar igual.
            {
                'DEBUG': 'True',
                'DB_ENGINE': 'postgresql',
                'DB_NAME': 'meteo',
                'DB_USER': 'u',
                'DB_HOST': 'h',
                'DB_PASS': 'p',
            },
        )

    def test_flags(self):
        self.assertIs(self.module.DEBUG, True)
        self.assertIs(self.module.IS_PRODUCTION, False)

    def test_no_secure_cookies(self):
        self.assert_no_secure_cookies(self.module)

    def test_debug_toolbar_enabled(self):
        self.assert_debug_toolbar(self.module)

    def test_static_storage_is_plain(self):
        self.assertEqual(self.module.STORAGES['staticfiles']['BACKEND'], STATIC_FILES_STORAGE)

    def test_whitenoise_middleware_removed(self):
        self.assertNotIn(base.whitenoise_middleware, self.module.MIDDLEWARE)

    def test_sqlite_wins_over_db_engine_env(self):
        """Riesgo del doc de diseño: con DB_ENGINE en `.env`, dev no conecta a la DB real."""
        self.assertEqual(self.module.DATABASES['default']['ENGINE'], SQLITE_ENGINE)

    def test_local_synop_simulations(self):
        self.assertIs(self.module.OBS_LOCAL_ONLY_DEFAULT, True)

    def test_console_email_by_default(self):
        """Sin `EMAIL_BACKEND` en el entorno, dev cae a consola (base defaultea SMTP)."""
        self.assertEqual(self.module.EMAIL_BACKEND, CONSOLE_EMAIL_BACKEND)

    def test_explicit_email_backend_wins(self):
        """Un valor explícito NO se pisa: desde dev se prueba envío real (MailHog, etc.)."""
        module = load_profile(
            'config.settings.dev',
            {'DEBUG': 'True', 'EMAIL_BACKEND': CUSTOM_EMAIL_BACKEND},
        )
        self.assertEqual(module.EMAIL_BACKEND, CUSTOM_EMAIL_BACKEND)


class TestingProfileTests(SecureCookieAssertionsMixin, DebugToolbarAssertionsMixin, SimpleTestCase):
    """Sin `DEBUG` y sin `PRODUCTION`: es CI, no "dev con la toolbar apagada"."""

    def setUp(self):
        self.module = load_profile('config.settings.testing', {'DEBUG': 'False'})

    def test_flags(self):
        self.assertIs(self.module.DEBUG, False)
        self.assertIs(self.module.IS_PRODUCTION, False)

    def test_secure_cookies(self):
        self.assert_secure_cookies(self.module)

    def test_no_debug_toolbar(self):
        self.assert_no_debug_toolbar(self.module)

    def test_static_storage_is_plain(self):
        self.assertEqual(self.module.STORAGES['staticfiles']['BACKEND'], STATIC_FILES_STORAGE)

    def test_whitenoise_middleware_removed(self):
        self.assertNotIn(base.whitenoise_middleware, self.module.MIDDLEWARE)

    def test_sqlite_without_db_engine(self):
        self.assertEqual(self.module.DATABASES['default']['ENGINE'], SQLITE_ENGINE)

    def test_db_engine_env_still_wins(self):
        """A diferencia de dev: acá `DB_ENGINE` sí define la base de datos."""
        module = load_profile(
            'config.settings.testing',
            {
                'DEBUG': 'False',
                'DB_ENGINE': 'postgresql',
                'DB_NAME': 'meteo',
                'DB_USER': 'u',
                'DB_HOST': 'h',
                'DB_PASS': 'p',
            },
        )
        self.assertEqual(module.DATABASES['default']['ENGINE'], 'django.db.backends.postgresql')

    def test_random_secret_key_fallback(self):
        """013-check-deploy-ci afirma que CI no debe fallar por una clave ausente."""
        self.assertTrue(self.module.SECRET_KEY)

    def test_ftp_simulations_off(self):
        self.assertIs(self.module.OBS_LOCAL_ONLY_DEFAULT, False)


class ProductionProfileTests(
    SecureCookieAssertionsMixin, DebugToolbarAssertionsMixin, SimpleTestCase
):
    """`PRODUCTION` en el entorno: fail-closed y WhiteNoise, sin depender de `DEBUG`."""

    DB_ENV = {
        'PRODUCTION': '1',
        'DB_ENGINE': 'postgresql',
        'DB_NAME': 'meteo',
        'DB_USER': 'u',
        'DB_HOST': 'h',
        'DB_PASS': 'p',
        **secret_env(),
    }

    def setUp(self):
        self.module = load_profile('config.settings.production', self.DB_ENV)

    def test_is_production(self):
        self.assertIs(self.module.IS_PRODUCTION, True)

    def test_secure_cookies(self):
        self.assert_secure_cookies(self.module)

    def test_no_debug_toolbar(self):
        self.assert_no_debug_toolbar(self.module)

    def test_manifest_static_storage(self):
        self.assertEqual(self.module.STORAGES['staticfiles']['BACKEND'], MANIFEST_STORAGE)

    def test_whitenoise_middleware_present_and_early(self):
        middleware = self.module.MIDDLEWARE
        self.assertIn(base.whitenoise_middleware, middleware)
        # El bloque de producción inserta WhiteNoise en MIDDLEWARE[1] si falta; la
        # lista base ya lo trae, así que hoy la inserción no ocurre. Se fija la
        # posición efectiva, no la intención del `insert`.
        self.assertEqual(middleware.index(base.whitenoise_middleware), 2)
        self.assertEqual(middleware[0], 'django.middleware.security.SecurityMiddleware')

    def test_database_built_from_db_engine(self):
        database = self.module.DATABASES['default']
        self.assertEqual(database['ENGINE'], 'django.db.backends.postgresql')
        self.assertEqual(database['NAME'], 'meteo')
        self.assertEqual(database['PORT'], '5432')
        self.assertEqual(database['CONN_MAX_AGE'], 600)

    def test_fail_closed_without_db_engine(self):
        """Con claves pero sin DB_ENGINE, producción no arranca (nunca cae a sqlite)."""
        with self.assertRaises(ImproperlyConfigured) as ctx:
            load_profile('config.settings.production', {'PRODUCTION': '1', **secret_env()})
        self.assertIn('DB_ENGINE', str(ctx.exception))

    def test_missing_secret_key_raises_before_database(self):
        """Sin claves y sin DB_ENGINE, el primer error es el de SECRET_KEY (orden del monolito)."""
        with self.assertRaises(ImproperlyConfigured) as ctx:
            load_profile('config.settings.production', {'PRODUCTION': '1'})
        self.assertIn('SECRET_KEY', str(ctx.exception))

    def test_debug_is_pinned_false(self):
        """`DEBUG=True` en el entorno no se hereda: producción lo pinea en False.

        Sin el pin, un `DEBUG=True` colado en el `.env` de producción publicaría
        tracebacks con paths del servidor.
        """
        module = load_profile('config.settings.production', {**self.DB_ENV, 'DEBUG': 'True'})
        self.assertIs(module.DEBUG, False)

    def test_console_email_backend_is_rejected(self):
        """Rama NEGATIVA del assert: consola en producción es un `.env` regenerable.

        El pie real no es "dev usa consola", es "producción usa consola en silencio":
        los correos se descartan sin un solo error.
        """
        with self.assertRaises(ImproperlyConfigured) as ctx:
            load_profile(
                'config.settings.production',
                {**self.DB_ENV, 'EMAIL_BACKEND': CONSOLE_EMAIL_BACKEND},
            )
        message = str(ctx.exception)
        self.assertIn(CONSOLE_EMAIL_BACKEND, message)
        self.assertIn('generate_env --production', message)

    def test_real_email_backends_are_accepted(self):
        """Rama POSITIVA del assert: todo backend menos consola pasa."""
        for backend in (DJANGO_SMTP_BACKEND, CUSTOM_EMAIL_BACKEND):
            with self.subTest(backend=backend):
                module = load_profile(
                    'config.settings.production', {**self.DB_ENV, 'EMAIL_BACKEND': backend}
                )
                self.assertEqual(module.EMAIL_BACKEND, backend)

    def test_ftp_simulations_off(self):
        self.assertIs(self.module.OBS_LOCAL_ONLY_DEFAULT, False)


class EphemeralSecretKeyFallbackTests(SimpleTestCase):
    """El fallback a clave efímera se queda (es el bypass de bootstrap) pero avisa.

    Ver odd/tasks/harden-settings-profiles-deploy-gate.md: `generate_env` es un
    management command y `manage.py` importa los settings antes de despacharlo,
    así que fallar cerrado aquí dejaría sin arranque al generador de claves.
    """

    WARNING = 'EphemeralSecretKeyWarning'

    def reload_base(self, env):
        """Recarga `base` con `env` como único entorno, capturando los warnings.

        `importlib.reload` borra `__warningregistry__`, así que el aviso se
        vuelve a emitir en cada recarga: por eso se usa `simplefilter('always')`.
        """
        with (
            mock.patch.dict(os.environ, env, clear=True),
            mock.patch('dotenv.load_dotenv'),
            warnings.catch_warnings(record=True) as caught,
        ):
            warnings.simplefilter('always')
            module = importlib.reload(base)
        return module, caught

    def warned(self, caught):
        return [w for w in caught if w.category.__name__ == self.WARNING]

    def test_missing_key_falls_back_and_warns(self):
        """Sin clave descifrable: cae a efímera Y deja un warning accionable."""
        module, caught = self.reload_base({'DEBUG': 'True'})
        self.assertTrue(module.SECRET_KEY)
        warned = self.warned(caught)
        self.assertEqual(len(warned), 1, 'el fallback tiene que avisar exactamente una vez')
        self.assertIn('generate_env', str(warned[0].message))

    def test_key_generator_can_still_boot(self):
        """La paradoja de bootstrap: `base` no puede fail-closed, o `generate_env` no arranca.

        Este test es la razón de que el test anterior espere un warning y no un raise.
        """
        module, caught = self.reload_base({'DEBUG': 'True'})
        self.assertTrue(module.SECRET_KEY)
        self.assertTrue(self.warned(caught), 'y el bypass tiene que seguir siendo visible')

    def test_valid_pair_does_not_warn(self):
        """Con un par Fernet válido el fallback no se alcanza: nada que avisar."""
        _module, caught = self.reload_base({'DEBUG': 'False', **secret_env()})
        self.assertEqual(self.warned(caught), [])


class DispatcherTests(SimpleTestCase):
    """La restricción dura: el perfil lo eligen las MISMAS variables de antes."""

    def test_flags_are_read_from_the_environment(self):
        from config import settings

        self.assertIs(settings.IS_PRODUCTION, 'PRODUCTION' in os.environ)
        self.assertIs(settings.DEBUG, os.getenv('DEBUG', 'False') == 'True')

    def test_production_profile_loads_without_the_dispatcher(self):
        """`DJANGO_SETTINGS_MODULE=config.settings.production` no pasa por el dispatcher."""
        env = {'PRODUCTION': '1', **secret_env(), **ProductionProfileTests.DB_ENV}
        module = load_profile('config.settings.production', env)
        self.assertEqual(module.__name__, 'config.settings.production')
        self.assertIs(module.IS_PRODUCTION, True)
