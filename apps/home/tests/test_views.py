from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.meteo.models import WeatherReport


class IndexViewTests(TestCase):
    def test_index_returns_200(self):
        response = self.client.get(reverse('home:index'))
        self.assertEqual(response.status_code, 200)

    def test_index_uses_correct_template(self):
        response = self.client.get(reverse('home:index'))
        self.assertTemplateUsed(response, 'pages/home/index.html')


class PublicServiceListViewTests(TestCase):
    def test_public_services_returns_200(self):
        response = self.client.get(reverse('home:services_public'))
        self.assertEqual(response.status_code, 200)


class SatelliteViewTests(TestCase):
    @patch('apps.home.views.satelites.views.requests.get')
    def test_satellite_view_returns_200(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'products': []}
        response = self.client.get(reverse('home:satellite'))
        self.assertEqual(response.status_code, 200)


class ScientificPublicationListViewTests(TestCase):
    def test_publications_returns_200(self):
        response = self.client.get(reverse('home:publications'))
        self.assertEqual(response.status_code, 200)


class WeatherReportHomeTests(TestCase):
    def test_today_returns_200_when_exists(self):
        user = User.objects.create_user('test', 't@t.com', 'pass', first_name='T', last_name='U')
        WeatherReport.objects.create(user=user, summary='Test', report_type='today')
        response = self.client.get(reverse('home:weather_today'))
        self.assertEqual(response.status_code, 200)

    def test_today_returns_200_when_no_data(self):
        response = self.client.get(reverse('home:weather_today'))
        self.assertEqual(response.status_code, 200)

    def test_tomorrow_returns_200_when_exists(self):
        user = User.objects.create_user('test2', 't2@t.com', 'pass', first_name='T', last_name='U')
        WeatherReport.objects.create(user=user, summary='Test', report_type='tomorrow')
        response = self.client.get(reverse('home:weather_tomorrow'))
        self.assertEqual(response.status_code, 200)

    def test_tomorrow_returns_200_when_no_data(self):
        response = self.client.get(reverse('home:weather_tomorrow'))
        self.assertEqual(response.status_code, 200)

    def test_commentary_returns_200_when_exists(self):
        user = User.objects.create_user('test3', 't3@t.com', 'pass', first_name='T', last_name='U')
        WeatherReport.objects.create(user=user, summary='Test', report_type='commentary')
        response = self.client.get(reverse('home:weather_commentary'))
        self.assertEqual(response.status_code, 200)

    def test_commentary_returns_200_when_no_data(self):
        response = self.client.get(reverse('home:weather_commentary'))
        self.assertEqual(response.status_code, 200)

    def test_note_returns_200_when_exists(self):
        user = User.objects.create_user('test4', 't4@t.com', 'pass', first_name='T', last_name='U')
        WeatherReport.objects.create(user=user, summary='Test', report_type='note')
        response = self.client.get(reverse('home:weather_note'))
        self.assertEqual(response.status_code, 200)

    def test_note_returns_200_when_no_data(self):
        response = self.client.get(reverse('home:weather_note'))
        self.assertEqual(response.status_code, 200)
