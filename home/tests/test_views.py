from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from dashboard.models import WeatherReport


class IndexViewTests(TestCase):
    def test_index_returns_200(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_index_uses_correct_template(self):
        response = self.client.get(reverse('index'))
        self.assertTemplateUsed(response, 'pages/home/index.html')


class PublicServiceListViewTests(TestCase):
    def test_public_services_returns_200(self):
        response = self.client.get(reverse('servicios_publicos'))
        self.assertEqual(response.status_code, 200)


class SatelliteViewTests(TestCase):
    @patch('home.views.satelites.views.requests.get')
    def test_satellite_view_returns_200(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'products': []}
        response = self.client.get(reverse('satelites'))
        self.assertEqual(response.status_code, 200)


class ScientificPublicationListViewTests(TestCase):
    def test_publications_returns_200(self):
        response = self.client.get(reverse('publicaciones_cientificas'))
        self.assertEqual(response.status_code, 200)


class WeatherReportHomeTests(TestCase):
    def test_today_returns_200_when_exists(self):
        user = User.objects.create_user('test', 't@t.com', 'pass', first_name='T', last_name='U')
        WeatherReport.objects.create(user=user, date=timezone.now(), summary='Test', type='today')
        response = self.client.get(reverse('tiempo_h'))
        self.assertEqual(response.status_code, 200)

    def test_today_returns_200_when_no_data(self):
        response = self.client.get(reverse('tiempo_h'))
        self.assertEqual(response.status_code, 200)

    def test_tomorrow_returns_200_when_exists(self):
        user = User.objects.create_user('test2', 't2@t.com', 'pass', first_name='T', last_name='U')
        WeatherReport.objects.create(user=user, date=timezone.now(), summary='Test', type='tomorrow')
        response = self.client.get(reverse('tiempo_m'))
        self.assertEqual(response.status_code, 200)

    def test_tomorrow_returns_200_when_no_data(self):
        response = self.client.get(reverse('tiempo_m'))
        self.assertEqual(response.status_code, 200)

    def test_commentary_returns_200_when_exists(self):
        user = User.objects.create_user('test3', 't3@t.com', 'pass', first_name='T', last_name='U')
        WeatherReport.objects.create(user=user, date=timezone.now(), summary='Test', type='commentary')
        response = self.client.get(reverse('comentario_tiempo'))
        self.assertEqual(response.status_code, 200)

    def test_commentary_returns_200_when_no_data(self):
        response = self.client.get(reverse('comentario_tiempo'))
        self.assertEqual(response.status_code, 200)

    def test_note_returns_200_when_exists(self):
        user = User.objects.create_user('test4', 't4@t.com', 'pass', first_name='T', last_name='U')
        WeatherReport.objects.create(user=user, date=timezone.now(), summary='Test', type='note')
        response = self.client.get(reverse('nota_meteorologica'))
        self.assertEqual(response.status_code, 200)

    def test_note_returns_200_when_no_data(self):
        response = self.client.get(reverse('nota_meteorologica'))
        self.assertEqual(response.status_code, 200)
