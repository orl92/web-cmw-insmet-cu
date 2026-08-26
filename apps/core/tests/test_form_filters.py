from datetime import datetime, time

from django.test import TestCase

from apps.core.templatetags import form_filters


class ToTimeValueTest(TestCase):
    def test_time_object_renders_12h_ampm(self):
        self.assertEqual(form_filters.to_time_value(time(6, 30)), '06:30 AM')
        self.assertEqual(form_filters.to_time_value(time(19, 30)), '07:30 PM')
        self.assertEqual(form_filters.to_time_value(time(0, 0)), '12:00 AM')
        self.assertEqual(form_filters.to_time_value(time(12, 0)), '12:00 PM')

    def test_datetime_object_renders_12h_ampm(self):
        self.assertEqual(
            form_filters.to_time_value(datetime(2026, 8, 5, 2, 15)), '02:15 AM'
        )
        self.assertEqual(
            form_filters.to_time_value(datetime(2026, 8, 5, 14, 30)), '02:30 PM'
        )

    def test_empty_returns_empty(self):
        self.assertEqual(form_filters.to_time_value(None), '')
        self.assertEqual(form_filters.to_time_value(''), '')

    def test_string_redisplay_normalizes_12h_and_24h(self):
        self.assertEqual(form_filters.to_time_value('06:30 AM'), '06:30 AM')
        self.assertEqual(form_filters.to_time_value('18:30'), '06:30 PM')
        self.assertEqual(form_filters.to_time_value('07:30 PM'), '07:30 PM')

    def test_unparseable_string_preserved(self):
        self.assertEqual(form_filters.to_time_value('no-soy-hora'), 'no-soy-hora')
