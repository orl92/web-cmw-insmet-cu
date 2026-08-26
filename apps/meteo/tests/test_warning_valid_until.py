"""Tests for the Warning.valid_until fix (016-public-ui-ux, Phase 3).

Covers:
- WarningForm accepts the 12h Tempus string and yields an aware America/Havana value
  (no -4h shift).
- A naive valid_until saved via the ORM is stored aware (Django normalizes under
  USE_TZ=True).
"""

import datetime
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.test import TestCase

from apps.meteo.forms.warning import WarningForm
from apps.meteo.models import Warning

HAVANA = ZoneInfo('America/Havana')


class WarningValidUntilFormTests(TestCase):
    def test_form_accepts_12h_tempus_string_as_aware_havana(self):
        form = WarningForm(
            data={'summary': 'Resumen de prueba', 'valid_until': '05/08/2026 02:30 PM'}
        )
        self.assertTrue(form.is_valid(), form.errors)
        value = form.cleaned_data['valid_until']
        self.assertIsNotNone(value.tzinfo)
        self.assertEqual(value.astimezone(HAVANA).utcoffset(), datetime.timedelta(hours=-4))
        # Wall-clock preserved: 14:30 Havana, not shifted to 10:30.
        self.assertEqual(value.astimezone(HAVANA).hour, 14)
        self.assertEqual(value.astimezone(HAVANA).minute, 30)

    def test_form_accepts_iso_format(self):
        form = WarningForm(data={'summary': 'Resumen ISO', 'valid_until': '2026-08-05T14:30'})
        self.assertTrue(form.is_valid(), form.errors)


class WarningValidUntilModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('warnuser', 'warn@test.com', 'pass')

    def test_save_make_aware_naive_valid_until(self):
        naive = datetime.datetime(2026, 8, 5, 14, 30)  # naive
        warning = Warning(
            user=self.user,
            warning_type='early',
            summary='Aviso naive',
            valid_until=naive,
        )
        warning.save()
        warning.refresh_from_db()
        self.assertIsNotNone(warning.valid_until.tzinfo)
        self.assertEqual(warning.valid_until.astimezone(HAVANA).hour, 14)

    def test_save_keeps_already_aware_value(self):
        aware = datetime.datetime(2026, 8, 5, 14, 30, tzinfo=HAVANA)
        warning = Warning.objects.create(
            user=self.user,
            warning_type='storm',
            summary='Aviso aware',
            valid_until=aware,
        )
        warning.refresh_from_db()
        self.assertEqual(warning.valid_until.astimezone(HAVANA).hour, 14)


class WarningDateTimeWidgetRenderTests(TestCase):
    def test_initial_render_uses_english_ampm(self):
        form = WarningForm(initial={'valid_until': datetime.datetime(2026, 8, 5, 14, 30)})
        rendered = form.as_p()
        self.assertIn('value="05/08/2026 02:30 PM"', rendered)
        self.assertNotIn('a. m.', rendered)
