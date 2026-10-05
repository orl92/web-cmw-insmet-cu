from datetime import UTC, datetime
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.core.models import SiteConfiguration
from apps.meteo.models import ForecastExtendedDay, ForecastRegions, Forecasts


def _disable_maintenance_mode():
    SiteConfiguration.objects.update_or_create(defaults={'maintenance_mode': False})


class ForecastAPILocaldateTests(TestCase):
    """Regression tests for the default-date branch of ForecastAPIView.

    NOTE: ``apps/api/urls.py`` routes only ``forecast/<str:date>/``, so the
    ``date is None`` branch is NOT reachable through HTTP today. These are
    contract tests on the view method, not end-to-end coverage. They exist so
    that if the route is ever relaxed to make the date optional, the default
    already resolves to the local day.

    Freezes time so UTC date differs from Havana local date:
    - UTC: 2026-10-04T02:30:00+00:00
    - Havana local: 2026-10-03 22:30:00-04:00
    - localdate() should be 2026-10-03, not 2026-10-04
    """

    FIXED_UTC = datetime(2026, 10, 4, 2, 30, 0, tzinfo=UTC)

    def setUp(self):
        _disable_maintenance_mode()

    def _create_forecast(self, forecast_date):
        forecast = Forecasts.objects.create(
            date=forecast_date,
            lp='Luna Nueva',
            nlp='Cuarto Creciente',
            nlpd=forecast_date,
            sunrise='06:30',
            sunset='18:30',
            uv_index=5,
        )
        for region in ('north', 'interior', 'south'):
            for period in ('morning', 'afternoon', 'night'):
                ForecastRegions.objects.create(
                    forecast=forecast,
                    region=region,
                    period=period,
                    temp=25,
                    weather='PN',
                    wind_dir='N',
                    wind_speed='10',
                )
        for i in range(1, 6):
            ForecastExtendedDay.objects.create(
                forecast=forecast,
                day_number=i,
                date=forecast_date,
                min_temp=20,
                max_temp=30,
                weather='PN',
            )
        return forecast

    def _call_get_without_date(self):
        from apps.api.views import ForecastAPIView

        view = ForecastAPIView()
        request = type('Req', (), {'GET': {}})()
        view.request = request
        # APIView.initial() sets this during dispatch(); calling get() directly
        # bypasses it, and get_serializer() needs it.
        view.format_kwarg = None
        return view.get(request, date=None)

    def test_default_resolves_to_local_date_when_only_local_forecast_exists(self):
        # Only the local-day forecast exists. The fixed code finds it (200);
        # the buggy UTC-date default finds nothing (404).
        with patch('django.utils.timezone.now', return_value=self.FIXED_UTC):
            self.assertEqual(timezone.localdate(), datetime(2026, 10, 3).date())
            self._create_forecast(timezone.localdate())

            resp = self._call_get_without_date()

        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.data)

    def test_default_does_not_fall_back_to_the_utc_day_forecast(self):
        # Only the UTC-day forecast exists. The fixed code must NOT serve it
        # as "today" (404); the buggy default would return it (200).
        with patch('django.utils.timezone.now', return_value=self.FIXED_UTC):
            self._create_forecast(datetime(2026, 10, 4).date())

            resp = self._call_get_without_date()

        self.assertEqual(resp.status_code, 404)
