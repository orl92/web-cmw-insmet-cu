from datetime import UTC, datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.models import SiteConfiguration
from apps.meteo.models import ForecastExtendedDay, ForecastRegions, Forecasts


def _disable_maintenance_mode():
    SiteConfiguration.objects.update_or_create(defaults={'maintenance_mode': False})


class ForecastLocaldateTests(TestCase):
    """Regression tests for localdate vs UTC date edge case.

    Freeze an aware UTC datetime whose local Havana time is 22:30 on a
    fixed local date but whose UTC date is the following day:
    - UTC: 2026-10-04T02:30:00+00:00
    - Havana (America/Havana, UTC-4): 2026-10-03 22:30:00-04:00
    - UTC date: 2026-10-04
    - Local date (timezone.localdate()): 2026-10-03
    """

    FIXED_UTC = datetime(2026, 10, 4, 2, 30, 0, tzinfo=UTC)

    def setUp(self):
        _disable_maintenance_mode()
        self.admin = User.objects.create_superuser(
            'forecastadmin',
            'forecastadmin@example.com',
            'pass',
            first_name='Admin',
            last_name='User',
        )

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

    def test_parse_date_filter_defaults_to_local_date(self):
        from apps.meteo.views.forecast import ForecastsListView

        with patch('django.utils.timezone.now', return_value=self.FIXED_UTC):
            local_date = timezone.localdate()
            resolved = ForecastsListView._parse_date_filter(None)
            self.assertEqual(resolved, local_date)
            self.assertEqual(local_date, datetime(2026, 10, 3).date())
            self.assertNotEqual(resolved, datetime(2026, 10, 4).date())

    def test_get_date_value_defaults_to_local_date(self):
        from apps.meteo.views.forecast import AllForecastCreateView

        with patch('django.utils.timezone.now', return_value=self.FIXED_UTC):
            view = AllForecastCreateView()
            view.request = type('Req', (), {'POST': {}, 'GET': {}})()
            resolved = view.get_date_value()
            local_date = timezone.localdate()
            self.assertEqual(resolved, local_date)
            self.assertEqual(local_date, datetime(2026, 10, 3).date())
            self.assertNotEqual(resolved, datetime(2026, 10, 4).date())

    def test_list_view_filters_by_local_date_not_utc(self):
        with patch('django.utils.timezone.now', return_value=self.FIXED_UTC):
            local_date = timezone.localdate()  # 2026-10-03
            utc_date = datetime(2026, 10, 4).date()

            self._create_forecast(local_date)
            self._create_forecast(utc_date)

            self.client.force_login(self.admin)
            url = reverse('meteo:pronostico_list')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['has_data'])
            forecasts = response.context['forecasts']
            self.assertEqual(forecasts.count(), 1)
            self.assertEqual(forecasts.first().date, local_date)

    def test_create_view_prefills_local_date(self):
        with patch('django.utils.timezone.now', return_value=self.FIXED_UTC):
            self.client.force_login(self.admin)
            url = reverse('meteo:pronostico_create')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['date'], '2026-10-03')
