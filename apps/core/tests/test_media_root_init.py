"""Tests for media-root-init (014): move MEDIA_ROOT mkdir out of settings import."""

import importlib
import inspect
import pathlib
import tempfile

from django.test import TestCase


class SettingsImportNoSideEffectTest(TestCase):
    """REQ-1: config/settings.py must NOT create media/ at import time."""

    def test_no_mkdir_in_settings_source(self):
        """The import-time 'if not MEDIA_ROOT.exists(): MEDIA_ROOT.mkdir' branch is gone."""
        source = inspect.getsource(importlib.import_module('config.settings'))
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
