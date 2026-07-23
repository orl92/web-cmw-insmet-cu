from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.crm.models import Customer, Service, ServiceSubscription
from apps.dashboard.models import (
    Contract,
    EarlyWarning,
    Invoice,
    SiteConfiguration,
    StormWarning,
    TropicalCyclone,
    WeatherReport,
)


def _make_admin(username='admin', **kwargs):
    email = kwargs.pop('email', f'{username}@example.com')
    data = {'first_name': 'Admin', 'last_name': 'User'}
    data.update(kwargs)
    return User.objects.create_superuser(username, email, 'password', **data)


def _disable_maintenance():
    SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})


class DashboardViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('dashadmin')
        cls.url = reverse('dashboard:index')

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
        self.assertIn('income_billed_data', response.context)
        self.assertIn('income_paid_data', response.context)
        self.assertIn('selected_income_range', response.context)
        self.assertIn('active_subs', response.context)
        self.assertIn('active_subs_list', response.context)
        self.assertIn('expired_subs', response.context)
        self.assertIn('expired_subs_list', response.context)
        self.assertIn('month_income', response.context)
        self.assertIn('pending_subs', response.context)
        self.assertIn('pending_subs_list', response.context)
        self.assertIn('requested_subs_list', response.context)

    def _make_client_user(self, username='client'):
        user = User.objects.create_user(username, f'{username}@test.com', 'password',
                                         first_name='Test', last_name='Client')
        group, _ = Group.objects.get_or_create(name='Clientes')
        user.groups.add(group)
        return user

    def test_client_can_access_dashboard(self):
        user = self._make_client_user('client1')
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_non_staff_non_client_cannot_access(self):
        user = User.objects.create_user('regular', 'reg@test.com', 'password',
                                          first_name='Regular', last_name='User')
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_client_context_variables(self):
        user = self._make_client_user('client2')
        customer = Customer.objects.create(
            company_name='Cliente SA', reeup='123.1.12345', nit='12345678901',
            account='1234567890123456', address='Calle 123', phone='12345678',
            user=user, accept_terms=True,
        )
        svc = Service.objects.create(
            title='Test Service', summary='Desc', price=100,
            code='TS001', user=user,
        )
        ServiceSubscription.objects.create(
            customer=customer, service=svc,
            payment_status='paid', start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
        )
        ServiceSubscription.objects.create(
            customer=customer, service=svc,
            payment_status='pending',
        )
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertIn('is_client', response.context)
        self.assertTrue(response.context['is_client'])
        self.assertIn('client_active_subs', response.context)
        self.assertEqual(response.context['client_active_subs'].count(), 1)
        self.assertIn('client_pending_subs', response.context)
        self.assertEqual(response.context['client_pending_subs'].count(), 1)

    def test_client_show_commercial_false(self):
        user = self._make_client_user('client3')
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertIn('show_commercial', response.context)
        self.assertFalse(response.context['show_commercial'])



class ForecastCRUDTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('fcadmin')
        cls.list_url = reverse('dashboard:pronostico_list')
        cls.create_url = reverse('dashboard:pronostico_create')

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
        response = self.client.get(reverse('dashboard:tiempo_hoy_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Listado del Tiempo')

    def test_list_view_tomorrow(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('dashboard:tiempo_manana_list'))
        self.assertEqual(response.status_code, 200)

    def test_list_view_commentary(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('dashboard:comentario_tiempo_list'))
        self.assertEqual(response.status_code, 200)

    def test_list_view_note(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('dashboard:nota_meteorologica_list'))
        self.assertEqual(response.status_code, 200)

    def test_create_today(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        data = {'summary': 'Soleado', 'file': pdf}
        response = self.client.post(reverse('dashboard:tiempo_hoy_create'), data, follow=True)
        self.assertTrue(WeatherReport.objects.filter(report_type='today', summary='Soleado').exists())
        self.assertRedirects(response, reverse('dashboard:tiempo_hoy_list'))

    def test_create_tomorrow(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        data = {'summary': 'Lluvioso', 'file': pdf}
        response = self.client.post(reverse('dashboard:tiempo_manana_create'), data, follow=True)
        self.assertTrue(WeatherReport.objects.filter(report_type='tomorrow', summary='Lluvioso').exists())
        self.assertRedirects(response, reverse('dashboard:tiempo_manana_list'))

    def test_create_commentary(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        data = {'summary': 'Comentario', 'file': pdf}
        response = self.client.post(reverse('dashboard:comentario_tiempo_create'), data, follow=True)
        self.assertTrue(WeatherReport.objects.filter(report_type='commentary', summary='Comentario').exists())
        self.assertRedirects(response, reverse('dashboard:comentario_tiempo_list'))

    def test_create_note(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        data = {'summary': 'Nota', 'file': pdf}
        response = self.client.post(reverse('dashboard:nota_meteorologica_create'), data, follow=True)
        self.assertTrue(WeatherReport.objects.filter(report_type='note', summary='Nota').exists())
        self.assertRedirects(response, reverse('dashboard:nota_meteorologica_list'))

    def test_update_today(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('orig.pdf', b'%PDF-1.4 orig', content_type='application/pdf')
        r = WeatherReport.objects.create(user=self.admin, date=timezone.now(), summary='Original', report_type='today', file=pdf)
        url = reverse('dashboard:tiempo_hoy_update', args=[r.uuid])
        pdf2 = SimpleUploadedFile('new.pdf', b'%PDF-1.4 new', content_type='application/pdf')
        response = self.client.post(url, {'summary': 'Actualizado', 'file': pdf2}, follow=True)
        r.refresh_from_db()
        self.assertEqual(r.summary, 'Actualizado')
        self.assertRedirects(response, reverse('dashboard:tiempo_hoy_list'))

    def test_delete_today(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('del.pdf', b'%PDF-1.4 del', content_type='application/pdf')
        r = WeatherReport.objects.create(user=self.admin, date=timezone.now(), summary='Del', report_type='today', file=pdf)
        url = reverse('dashboard:tiempo_hoy_delete', args=[r.uuid])
        response = self.client.post(url, follow=True)
        self.assertFalse(WeatherReport.objects.filter(pk=r.pk).exists())
        self.assertRedirects(response, reverse('dashboard:tiempo_hoy_list'))


class EarlyWarningTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('ewadmin')
        cls.list_url = reverse('dashboard:alerta_temprana_list')
        cls.create_url = reverse('dashboard:alerta_temprana_create')

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 302)
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 302)

    def test_superuser_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)

    def test_list_contains_objects(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        valid_until = timezone.now() + timedelta(days=1)
        obj = EarlyWarning.objects.create(
            user=self.admin, summary='Test Early Warning',
            valid_until=valid_until, file=pdf,
        )
        response = self.client.get(self.list_url)
        self.assertContains(response, obj.summary)

    @patch('apps.dashboard.views.avisos.alertas_tempranas.views.mail_send')
    def test_create_redirects(self, mock_mail_send):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        valid_until = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        data = {'summary': 'New Early Warning', 'valid_until': valid_until, 'file': pdf}
        response = self.client.post(self.create_url, data, follow=True)
        self.assertTrue(EarlyWarning.objects.filter(summary='New Early Warning').exists())
        self.assertRedirects(response, self.list_url)

    @patch('apps.dashboard.views.avisos.alertas_tempranas.views.mail_send')
    def test_update_redirects(self, mock_mail_send):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('orig.pdf', b'%PDF-1.4 orig', content_type='application/pdf')
        valid_until = timezone.now() + timedelta(days=1)
        obj = EarlyWarning.objects.create(
            user=self.admin, summary='Original', valid_until=valid_until, file=pdf,
        )
        url = reverse('dashboard:alerta_temprana_update', args=[obj.uuid])
        pdf2 = SimpleUploadedFile('new.pdf', b'%PDF-1.4 new', content_type='application/pdf')
        valid_until2 = (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
        response = self.client.post(url, {
            'summary': 'Updated', 'valid_until': valid_until2, 'file': pdf2,
        }, follow=True)
        obj.refresh_from_db()
        self.assertEqual(obj.summary, 'Updated')
        self.assertRedirects(response, self.list_url)

    def test_delete_redirects(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('del.pdf', b'%PDF-1.4 del', content_type='application/pdf')
        valid_until = timezone.now() + timedelta(days=1)
        obj = EarlyWarning.objects.create(
            user=self.admin, summary='Delete Me', valid_until=valid_until, file=pdf,
        )
        url = reverse('dashboard:alerta_temprana_delete', args=[obj.uuid])
        response = self.client.post(url, follow=True)
        self.assertFalse(EarlyWarning.objects.filter(pk=obj.pk).exists())
        self.assertRedirects(response, self.list_url)


class TropicalCycloneTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('tcadmin')
        cls.list_url = reverse('dashboard:ciclon_tropical_list')
        cls.create_url = reverse('dashboard:ciclon_tropical_create')

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 302)
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 302)

    def test_superuser_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)

    def test_list_contains_objects(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        valid_until = timezone.now() + timedelta(days=1)
        obj = TropicalCyclone.objects.create(
            user=self.admin, summary='Test Cyclone',
            valid_until=valid_until, file=pdf,
        )
        response = self.client.get(self.list_url)
        self.assertContains(response, obj.summary)

    @patch('apps.dashboard.views.avisos.ciclones_tropicales.views.mail_send')
    def test_create_redirects(self, mock_mail_send):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        valid_until = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        data = {'summary': 'New Cyclone', 'valid_until': valid_until, 'file': pdf}
        response = self.client.post(self.create_url, data, follow=True)
        self.assertTrue(TropicalCyclone.objects.filter(summary='New Cyclone').exists())
        self.assertRedirects(response, self.list_url)

    @patch('apps.dashboard.views.avisos.ciclones_tropicales.views.mail_send')
    def test_update_redirects(self, mock_mail_send):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('orig.pdf', b'%PDF-1.4 orig', content_type='application/pdf')
        valid_until = timezone.now() + timedelta(days=1)
        obj = TropicalCyclone.objects.create(
            user=self.admin, summary='Original', valid_until=valid_until, file=pdf,
        )
        url = reverse('dashboard:ciclon_tropical_update', args=[obj.uuid])
        pdf2 = SimpleUploadedFile('new.pdf', b'%PDF-1.4 new', content_type='application/pdf')
        valid_until2 = (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
        response = self.client.post(url, {
            'summary': 'Updated', 'valid_until': valid_until2, 'file': pdf2,
        }, follow=True)
        obj.refresh_from_db()
        self.assertEqual(obj.summary, 'Updated')
        self.assertRedirects(response, self.list_url)

    def test_delete_redirects(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('del.pdf', b'%PDF-1.4 del', content_type='application/pdf')
        valid_until = timezone.now() + timedelta(days=1)
        obj = TropicalCyclone.objects.create(
            user=self.admin, summary='Delete Me', valid_until=valid_until, file=pdf,
        )
        url = reverse('dashboard:ciclon_tropical_delete', args=[obj.uuid])
        response = self.client.post(url, follow=True)
        self.assertFalse(TropicalCyclone.objects.filter(pk=obj.pk).exists())
        self.assertRedirects(response, self.list_url)


class StormWarningTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('swadmin')
        cls.list_url = reverse('dashboard:tormenta_list')
        cls.create_url = reverse('dashboard:tormenta_create')

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 302)
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 302)

    def test_superuser_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)

    def test_list_contains_objects(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        valid_until = timezone.now() + timedelta(days=1)
        obj = StormWarning.objects.create(
            user=self.admin, summary='Test Storm',
            valid_until=valid_until, file=pdf,
        )
        response = self.client.get(self.list_url)
        self.assertContains(response, obj.summary)

    @patch('apps.dashboard.views.avisos.tormentas.views.mail_send')
    def test_create_redirects(self, mock_mail_send):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        valid_until = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        data = {'summary': 'New Storm', 'valid_until': valid_until, 'file': pdf}
        response = self.client.post(self.create_url, data, follow=True)
        self.assertTrue(StormWarning.objects.filter(summary='New Storm').exists())
        self.assertRedirects(response, self.list_url)

    @patch('apps.dashboard.views.avisos.tormentas.views.mail_send')
    def test_update_redirects(self, mock_mail_send):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('orig.pdf', b'%PDF-1.4 orig', content_type='application/pdf')
        valid_until = timezone.now() + timedelta(days=1)
        obj = StormWarning.objects.create(
            user=self.admin, summary='Original', valid_until=valid_until, file=pdf,
        )
        url = reverse('dashboard:tormenta_update', args=[obj.uuid])
        pdf2 = SimpleUploadedFile('new.pdf', b'%PDF-1.4 new', content_type='application/pdf')
        valid_until2 = (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
        response = self.client.post(url, {
            'summary': 'Updated', 'valid_until': valid_until2, 'file': pdf2,
        }, follow=True)
        obj.refresh_from_db()
        self.assertEqual(obj.summary, 'Updated')
        self.assertRedirects(response, self.list_url)

    def test_delete_redirects(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('del.pdf', b'%PDF-1.4 del', content_type='application/pdf')
        valid_until = timezone.now() + timedelta(days=1)
        obj = StormWarning.objects.create(
            user=self.admin, summary='Delete Me', valid_until=valid_until, file=pdf,
        )
        url = reverse('dashboard:tormenta_delete', args=[obj.uuid])
        response = self.client.post(url, follow=True)
        self.assertFalse(StormWarning.objects.filter(pk=obj.pk).exists())
        self.assertRedirects(response, self.list_url)


class ContractCRUDTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('coadmin')
        cls.list_url = reverse('dashboard:contrato_list')
        cls.create_url = reverse('dashboard:contrato_create')
        user = User.objects.create_user('contractuser', 'contract@test.com', 'password')
        cls.customer = Customer.objects.create(
            company_name='Contract Corp', reeup='123.1.12345', nit='12345678901',
            account='1234567890123456', address='Calle 123', phone='12345678',
            user=user, accept_terms=True,
        )
        cls.service = Service.objects.create(
            title='Contract Svc', summary='Test', user=cls.admin,
            service_type='commercial', price=100, code='CS001',
        )
        cls.subscription = ServiceSubscription.objects.create(
            customer=cls.customer, service=cls.service,
            payment_status='paid', start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 302)
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 302)

    def test_superuser_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)

    def test_list_contains_objects(self):
        self.client.force_login(self.admin)
        Contract.objects.create(
            subscription=self.subscription, number='2025-0001',
            date=timezone.now().date(), commercial_registry='A09404',
        )
        response = self.client.get(self.list_url)
        self.assertContains(response, '2025-0001')

    def test_create_redirects(self):
        self.client.force_login(self.admin)
        data = {
            'subscription': self.subscription.pk,
            'number': '2025-0002',
            'date': timezone.now().date().strftime('%Y-%m-%d'),
            'commercial_registry': 'A09405',
        }
        response = self.client.post(self.create_url, data, follow=True)
        self.assertTrue(Contract.objects.filter(number='2025-0002').exists())
        self.assertRedirects(response, self.list_url)

    def test_delete_redirects(self):
        self.client.force_login(self.admin)
        contract = Contract.objects.create(
            subscription=self.subscription, number='2025-0003',
            date=timezone.now().date(), commercial_registry='A09406',
        )
        url = reverse('dashboard:contrato_delete', args=[contract.uuid])
        response = self.client.post(url, follow=True)
        contract.refresh_from_db()
        self.assertFalse(contract.record_active)
        self.assertRedirects(response, self.list_url)
