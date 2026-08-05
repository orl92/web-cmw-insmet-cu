import shutil
import tempfile

from django.conf import settings
from django.test.runner import DiscoverRunner


class IsolatedMediaRunner(DiscoverRunner):
    """Redirects MEDIA_ROOT to a temp dir for the whole suite and cleans up."""

    def setup_test_environment(self, **kwargs):
        self._tmp_media_root = tempfile.mkdtemp(prefix='opencode_test_media_')
        self._original_media_root = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = self._tmp_media_root
        super().setup_test_environment(**kwargs)

    def teardown_test_environment(self, **kwargs):
        super().teardown_test_environment(**kwargs)
        settings.MEDIA_ROOT = self._original_media_root
        shutil.rmtree(self._tmp_media_root, ignore_errors=True)
