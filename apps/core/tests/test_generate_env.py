import re
from io import StringIO
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

_COMMENTED_VAR = re.compile(r'^#\s*[A-Za-z_][A-Za-z0-9_]*\s*=')


class GenerateEnvCommandTests(TestCase):
    """Lock the generate_env UX: no commented variable lines, correct engine
    per environment, and never overwrite an existing .env without consent."""

    def setUp(self):
        self.env_path = settings.BASE_DIR / '.env'
        self.backup = self.env_path.read_text(encoding='utf-8') if self.env_path.exists() else None

    def tearDown(self):
        if self.backup is None:
            if self.env_path.exists():
                self.env_path.unlink()
        else:
            self.env_path.write_text(self.backup, encoding='utf-8')

    def test_development_generates_env_without_commented_vars(self):
        call_command('generate_env', '--development', stdout=StringIO())
        self.assertTrue(self.env_path.exists())
        content = self.env_path.read_text(encoding='utf-8')

        for line in content.splitlines():
            if _COMMENTED_VAR.match(line.strip()):
                self.fail(f'Comented variable assignment found: {line}')

        # Dev non-interactive uses SQLite and disables LDAP by default.
        self.assertIn('DB_ENGINE=sqlite3', content)
        self.assertNotIn('LDAP_SERVER_URI', content)

    def test_existing_env_not_overwritten_when_regenerate_declined(self):
        self.env_path.write_text('DEBUG=True\n', encoding='utf-8')
        with patch('builtins.input', return_value=''):
            call_command('generate_env', stdout=StringIO())
        self.assertEqual(self.env_path.read_text(encoding='utf-8'), 'DEBUG=True\n')
