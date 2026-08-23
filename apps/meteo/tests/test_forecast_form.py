from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.meteo.forms.forecast import (
    ForecastExtendedDayFormSet,
    ForecastRegionsFormSet,
    ForecastsForm,
)
from apps.meteo.models import Forecasts


class ForecastFormTimeTests(TestCase):
    def _base_data(self, **overrides):
        data = {
            'date': '2026-08-23',
            'lp': 'Luna Nueva',
            'nlp': 'Luna Nueva',
            'nlpd': '2026-08-24',
            'sunrise': '6:30 AM',
            'sunset': '7:30 PM',
            'uv_index': 5,
        }
        data.update(overrides)
        return data

    def test_time_parses_12h_format(self):
        form = ForecastsForm(data=self._base_data())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['sunrise'].hour, 6)
        self.assertEqual(form.cleaned_data['sunset'].hour, 19)

    def test_time_parses_24h_format(self):
        form = ForecastsForm(data=self._base_data(sunrise='06:30', sunset='19:30'))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['sunrise'].hour, 6)

    def test_sunrise_must_be_am(self):
        form = ForecastsForm(data=self._base_data(sunrise='6:30 PM'))
        self.assertFalse(form.is_valid())
        self.assertIn('sunrise', form.errors)

    def test_sunset_must_be_pm(self):
        form = ForecastsForm(data=self._base_data(sunset='7:30 AM'))
        self.assertFalse(form.is_valid())
        self.assertIn('sunset', form.errors)


class ForecastRegionTempValidationTests(TestCase):
    def setUp(self):
        self.forecast = Forecasts.objects.create(
            date='2026-08-23',
            lp='Luna Nueva',
            nlp='Luna Nueva',
            nlpd='2026-08-24',
            sunrise='06:30',
            sunset='19:30',
            uv_index=5,
        )

    def _region_data(self, **overrides):
        data = {
            'regions-TOTAL_FORMS': '1',
            'regions-INITIAL_FORMS': '0',
            'regions-MIN_NUM_FORMS': '0',
            'regions-MAX_NUM_FORMS': '9',
            'regions-0-region': 'north',
            'regions-0-period': 'morning',
            'regions-0-temp': '28',
            'regions-0-weather': 'N',
            'regions-0-wind_dir': 'N',
            'regions-0-wind_speed': '5',
            'regions-0-sea_note': 'TQ',
        }
        data.update(overrides)
        return data

    def test_temp_in_range_is_valid(self):
        formset = ForecastRegionsFormSet(self._region_data(), instance=self.forecast)
        self.assertTrue(formset.is_valid(), formset.errors)

    def test_temp_above_maximum_rejected(self):
        formset = ForecastRegionsFormSet(
            self._region_data(**{'regions-0-temp': '99'}), instance=self.forecast
        )
        self.assertFalse(formset.is_valid())

    def test_temp_below_minimum_rejected(self):
        formset = ForecastRegionsFormSet(
            self._region_data(**{'regions-0-temp': '-50'}), instance=self.forecast
        )
        self.assertFalse(formset.is_valid())


class ForecastExtendedDayValidationTests(TestCase):
    def setUp(self):
        self.forecast = Forecasts.objects.create(
            date='2026-08-23',
            lp='Luna Nueva',
            nlp='Luna Nueva',
            nlpd='2026-08-24',
            sunrise='06:30',
            sunset='19:30',
            uv_index=5,
        )

    def _extended_data(self, **overrides):
        data = {
            'extended_days-TOTAL_FORMS': '1',
            'extended_days-INITIAL_FORMS': '0',
            'extended_days-MIN_NUM_FORMS': '0',
            'extended_days-MAX_NUM_FORMS': '5',
            'extended_days-0-day_number': '1',
            'extended_days-0-date': '2026-08-24',
            'extended_days-0-min_temp': '20',
            'extended_days-0-max_temp': '30',
            'extended_days-0-weather': 'N',
        }
        data.update(overrides)
        return data

    def test_extended_valid(self):
        formset = ForecastExtendedDayFormSet(self._extended_data(), instance=self.forecast)
        self.assertTrue(formset.is_valid(), formset.errors)

    def test_extended_min_gt_max_rejected(self):
        formset = ForecastExtendedDayFormSet(
            self._extended_data(
                **{
                    'extended_days-0-min_temp': '30',
                    'extended_days-0-max_temp': '10',
                }
            ),
            instance=self.forecast,
        )
        self.assertFalse(formset.is_valid())


class ForecastEditRenderTests(TestCase):
    def test_edit_renders_24h_time_value(self):
        # El valor inicial va en 24h (HH:MM): Tempus y Django lo parsean sin
        # depender del locale del navegador (sin meridiano "a. m.").
        forecast = Forecasts.objects.create(
            date='2026-08-23',
            lp='Luna Nueva',
            nlp='Luna Nueva',
            nlpd='2026-08-24',
            sunrise='06:40',
            sunset='19:30',
            uv_index=5,
        )
        user = User.objects.create_superuser(
            'admin', 'admin@example.com', 'pw', first_name='Admin', last_name='Test'
        )
        self.client.force_login(user)
        resp = self.client.get(reverse('meteo:pronostico_update', args=[forecast.uuid]))
        self.assertContains(resp, 'value="06:40"')
        self.assertContains(resp, 'value="19:30"')
        self.assertNotContains(resp, '6:40 a')
