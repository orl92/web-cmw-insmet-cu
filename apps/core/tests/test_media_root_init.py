"""Tests for media-root-init (014): move MEDIA_ROOT mkdir out of settings import."""

import pathlib
import tempfile

from django.test import TestCase

import config.settings


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
    """REQ-2: CoreConfig.ready() creates MEDIA_ROOT idempotently."""

    def _invoke_ready_mkdir(self, media_root: pathlib.Path) -> None:
        """Call the mkdir logic that CoreConfig.ready() performs.

        We replicate the production path (Path(settings.MEDIA_ROOT).mkdir)
        to avoid needing to instantiate AppConfig from scratch.
        """
        from django.apps import apps

        config = apps.get_app_config('core')
        # Store original MEDIA_ROOT, swap to target, call ready(), restore
        from django.conf import settings

        original = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = str(media_root)
        try:
            config.ready()
        finally:
            settings.MEDIA_ROOT = original

    def test_ready_creates_directory(self):
        """ready() creates the media directory when it does not exist."""
        target = pathlib.Path(tempfile.mkdtemp()) / 'test_media'
        try:
            self.assertFalse(target.exists())
            self._invoke_ready_mkdir(target)
            self.assertTrue(target.is_dir())
        finally:
            if target.exists():
                target.rmdir()

    def test_ready_idempotent(self):
        """Calling ready() twice on the same path does not raise."""
        target = pathlib.Path(tempfile.mkdtemp()) / 'test_media_idem'
        try:
            self.assertFalse(target.exists())
            self._invoke_ready_mkdir(target)
            self._invoke_ready_mkdir(target)  # second call — must not raise
            self.assertTrue(target.is_dir())
        finally:
            if target.exists():
                target.rmdir()
