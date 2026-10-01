"""Tests for media-root-init (014): move MEDIA_ROOT mkdir out of settings import.

Also covers the regression that came out of it: `CoreConfig.ready()` must be
safe to invoke more than once in a process, which means the Huey signal
registration it performs has to be idempotent.
"""

import pathlib
import tempfile

from django.test import SimpleTestCase, TestCase
from huey import signals as huey_signals

import config.settings
from config.huey import huey


class SettingsImportNoSideEffectTest(TestCase):
    """REQ-1: the settings package must NOT create media/ at import time."""

    def _settings_sources(self):
        """Yield (name, source) for every module in the `config.settings` package.

        `config.settings` is a package, so `inspect.getsource` on it returns
        only `__init__.py`: a check scoped to the entry module would never
        reach the file where MEDIA_ROOT actually lives (`base.py`) and could
        not fail. Reading every module in the package is what gives the
        assertion reach.
        """
        package_dir = pathlib.Path(config.settings.__file__).resolve().parent
        modules = sorted(package_dir.glob('*.py'))
        self.assertTrue(modules, f'no settings modules found in {package_dir}')
        return [(path.name, path.read_text(encoding='utf-8')) for path in modules]

    def test_no_mkdir_in_any_settings_module(self):
        """No settings module contains the import-time MEDIA_ROOT.mkdir branch."""
        for name, source in self._settings_sources():
            with self.subTest(module=name):
                self.assertNotIn('MEDIA_ROOT.mkdir', source)
                self.assertNotIn('if not MEDIA_ROOT.exists():', source)


class CoreConfigReadyMediaRootTest(TestCase):
    """REQ-2: startup creates MEDIA_ROOT idempotently.

    `CoreConfig.ready()` delegates to `CoreConfig.ensure_media_root()`, which is
    what these tests exercise.
    """

    def _invoke_ensure_media_root(self, media_root: pathlib.Path) -> None:
        """Point MEDIA_ROOT at `media_root` and run the production mkdir.

        This IS the production path, not a replication of it: `ready()` delegates
        to `ensure_media_root()`, and that method reads `settings.MEDIA_ROOT` on
        every call, so swapping the setting exercises the very code startup runs.
        Calling it here also keeps these tests away from `ready()` itself, whose
        side effects (re-connecting the Huey signal receivers on every call) leak
        into unrelated tests.
        """
        from django.apps import apps

        config = apps.get_app_config('core')
        # Store original MEDIA_ROOT, swap to target, run mkdir, restore
        from django.conf import settings

        original = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = str(media_root)
        try:
            config.ensure_media_root()
        finally:
            settings.MEDIA_ROOT = original

    def test_ready_creates_directory(self):
        """Startup creates the media directory when it does not exist."""
        target = pathlib.Path(tempfile.mkdtemp()) / 'test_media'
        try:
            self.assertFalse(target.exists())
            self._invoke_ensure_media_root(target)
            self.assertTrue(target.is_dir())
        finally:
            if target.exists():
                target.rmdir()

    def test_ready_idempotent(self):
        """Running the mkdir twice on the same path does not raise."""
        target = pathlib.Path(tempfile.mkdtemp()) / 'test_media_idem'
        try:
            self.assertFalse(target.exists())
            self._invoke_ensure_media_root(target)
            self._invoke_ensure_media_root(target)  # second call — must not raise
            self.assertTrue(target.is_dir())
        finally:
            if target.exists():
                target.rmdir()


class TaskSignalRegistrationIdempotencyTest(SimpleTestCase):
    """`register_task_signals()` connects the receivers exactly once per process.

    Regression: the receivers used to be defined inside `ready()`, so every extra
    `ready()` call re-connected five more receivers on the `config.huey.huey`
    singleton. A single enqueue then ran each receiver N times and the invoice
    delivery log inflated `attempts`, breaking
    `test_invoice_delivery.ClaveLogicaTests.test_reintentar_actualiza_la_misma_fila`
    whenever `apps.core` ran before `apps.commercial`.

    Inspecting receivers: `huey.signals.SIGNAL_ENQUEUED` is a plain string, not a
    `Signal` instance, so it has no `.receivers`. Huey keeps the registry on the
    `Huey` instance as `huey._signal.receivers`, a dict mapping each signal name
    to the list of callables connected to it (plus an `'any'` bucket).
    """

    SIGNALS = (
        huey_signals.SIGNAL_ENQUEUED,
        huey_signals.SIGNAL_EXECUTING,
        huey_signals.SIGNAL_COMPLETE,
        huey_signals.SIGNAL_RETRYING,
        huey_signals.SIGNAL_ERROR,
    )

    def _receiver_count(self, signal_name: str) -> int:
        return len(huey._signal.receivers.get(signal_name, ()))

    def test_register_task_signals_es_idempotente(self):
        """Calling it twice does not add a second copy of the receivers."""
        from django.apps import apps

        config = apps.get_app_config('core')

        antes = {name: self._receiver_count(name) for name in self.SIGNALS}
        for name, count in antes.items():
            # Guard against a vacuous pass: if startup never connected anything,
            # "nothing grew" would be trivially true and prove nothing.
            self.assertGreaterEqual(count, 1, f'no hay receiver conectado para la señal {name!r}')

        config.register_task_signals()
        config.register_task_signals()

        for name in self.SIGNALS:
            with self.subTest(signal=name):
                self.assertEqual(self._receiver_count(name), antes[name])
