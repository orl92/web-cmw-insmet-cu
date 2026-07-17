from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from dashboard.models import (
    Customer,
    EarlyWarning,
    Province,
    SiteConfiguration,
    TropicalCyclone,
    WeatherReport,
)


def _make_admin(username='admin', **kwargs):
    email = kwargs.pop('email', f'{username}@example.com')
    data = {'first_name': 'Admin', 'last_name': 'User'}
    data.update(kwargs)
    return User.objects.create_superuser(username, email, 'password', **data)


def _disable_maintenance():
    SiteConfiguration.objects.get_or_create(pk=1, defaults={'maintenance_mode': False})


class DashboardViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('dashadmin')
        cls.url = reverse('dashboard')

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_superuser_can_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_analytics_context_variables_exist(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertIn('income_months', response.context)
        self.assertIn('income_data', response.context)
        self.assertIn('active_subs', response.context)
        self.assertIn('expired_subs', response.context)
        self.assertIn('alert_counts', response.context)
        self.assertIn('new_customers', response.context)
        self.assertIn('total_active_alerts', response.context)

    def test_new_customers_count(self):
        user = User.objects.create_user('cust1', date_joined=timezone.now())
        Customer.objects.create(
            company_name='Test Corp', reeup='123.1.12345', nit='12345678901',
            account='1234567890123456', address='Calle 123', phone='12345678',
            user=user, accept_terms=True,
        )
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.context['new_customers'], 1)

    def test_alert_counts(self):
        user = User.objects.create_user('alertuser')
        EarlyWarning.objects.create(user=user, summary='Test', valid_until=timezone.now() + timezone.timedelta(days=1))
        TropicalCyclone.objects.create(user=user, summary='Test', valid_until=timezone.now() + timezone.timedelta(days=1))
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.context['alert_counts']['early_warnings'], 1)
        self.assertEqual(response.context['alert_counts']['tropical_cyclones'], 1)
        self.assertEqual(response.context['total_active_alerts'], 2)


class ProvinceCRUDTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('provadmin')
        cls.list_url = reverse('provincias')
        cls.create_url = reverse('crear_provincia')

    def test_list_view(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Listado de Provincias')

    def test_create_province(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.create_url, {'name': 'TestProv', 'code': 'TP'}, follow=True)
        self.assertTrue(Province.objects.filter(name='TestProv').exists())
        self.assertRedirects(response, self.list_url)

    def test_update_province(self):
        self.client.force_login(self.admin)
        prov = Province.objects.create(name='OldName', code='ON')
        url = reverse('actualizar_provincia', args=[prov.uuid])
        response = self.client.post(url, {'name': 'NewName', 'code': 'NN'}, follow=True)
        prov.refresh_from_db()
        self.assertEqual(prov.name, 'NewName')

    def test_delete_province(self):
        self.client.force_login(self.admin)
        prov = Province.objects.create(name='DeleteMe', code='DM')
        url = reverse('eliminar_provincia', args=[prov.uuid])
        response = self.client.post(url, follow=True)
        self.assertFalse(Province.objects.filter(name='DeleteMe').exists())
        self.assertRedirects(response, self.list_url)


class StationCRUDTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('stnadmin')
        cls.prov = Province.objects.create(name='TestProv', code='TP')
        cls.list_url = reverse('estaciones')
        cls.create_url = reverse('crear_estacion')

    def test_list_view(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

    def test_create_station(self):
        self.client.force_login(self.admin)
        data = {
            'name': 'TestStation',
            'number': 999,
            'province': self.prov.pk,
            'latitude': 21.5,
            'longitude': -78.0,
        }
        response = self.client.post(self.create_url, data, follow=True)
        from dashboard.models import Station
        self.assertTrue(Station.objects.filter(name='TestStation').exists())


class ForecastCRUDTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('fcadmin')
        cls.list_url = reverse('pronosticos')
        cls.create_url = reverse('crear_pronostico')

    def test_list_view(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)


class WeatherReportCRUDTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('wradmin')

    def test_list_view_today(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('listado_tiempo_h'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Listado del Tiempo')

    def test_list_view_tomorrow(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('listado_tiempo_m'))
        self.assertEqual(response.status_code, 200)

    def test_list_view_commentary(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('listado_comentarios_tiempo'))
        self.assertEqual(response.status_code, 200)

    def test_list_view_note(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('listado_notas_meteorologicas'))
        self.assertEqual(response.status_code, 200)

    def test_create_today(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        data = {'summary': 'Soleado', 'file': pdf}
        response = self.client.post(reverse('crear_tiempo_h'), data, follow=True)
        self.assertTrue(WeatherReport.objects.filter(type='today', summary='Soleado').exists())
        self.assertRedirects(response, reverse('listado_tiempo_h'))

    def test_create_tomorrow(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        data = {'summary': 'Lluvioso', 'file': pdf}
        response = self.client.post(reverse('crear_tiempo_m'), data, follow=True)
        self.assertTrue(WeatherReport.objects.filter(type='tomorrow', summary='Lluvioso').exists())
        self.assertRedirects(response, reverse('listado_tiempo_m'))

    def test_create_commentary(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        data = {'summary': 'Comentario', 'file': pdf}
        response = self.client.post(reverse('crear_comentario_tiempo'), data, follow=True)
        self.assertTrue(WeatherReport.objects.filter(type='commentary', summary='Comentario').exists())
        self.assertRedirects(response, reverse('listado_comentarios_tiempo'))

    def test_create_note(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        data = {'summary': 'Nota', 'file': pdf}
        response = self.client.post(reverse('crear_nota_meteorologica'), data, follow=True)
        self.assertTrue(WeatherReport.objects.filter(type='note', summary='Nota').exists())
        self.assertRedirects(response, reverse('listado_notas_meteorologicas'))

    def test_update_today(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('orig.pdf', b'%PDF-1.4 orig', content_type='application/pdf')
        r = WeatherReport.objects.create(user=self.admin, date=timezone.now(), summary='Original', type='today', file=pdf)
        url = reverse('actualizar_tiempo_h', args=[r.uuid])
        pdf2 = SimpleUploadedFile('new.pdf', b'%PDF-1.4 new', content_type='application/pdf')
        response = self.client.post(url, {'summary': 'Actualizado', 'file': pdf2}, follow=True)
        r.refresh_from_db()
        self.assertEqual(r.summary, 'Actualizado')
        self.assertRedirects(response, reverse('listado_tiempo_h'))

    def test_delete_today(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('del.pdf', b'%PDF-1.4 del', content_type='application/pdf')
        r = WeatherReport.objects.create(user=self.admin, date=timezone.now(), summary='Del', type='today', file=pdf)
        url = reverse('eliminar_tiempo_h', args=[r.uuid])
        response = self.client.post(url, follow=True)
        self.assertFalse(WeatherReport.objects.filter(pk=r.pk).exists())
        self.assertRedirects(response, reverse('listado_tiempo_h'))
