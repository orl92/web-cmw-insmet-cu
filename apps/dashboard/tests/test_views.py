import json
from datetime import time

from django.contrib.auth.models import ContentType, Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.commercial.models import (
    Customer, Invoice, Service, ServiceSubscription,
)
from apps.core.models import SiteConfiguration
from apps.meteo.models import Forecasts, ForecastRegions, Warning


def disable_maintenance_mode():
    SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})


def _make_user(username, **kwargs):
    data = {
        'first_name': 'Test', 'last_name': 'User',
        'email': f'{username}@example.com',
    }
    data.update(kwargs)
    return User.objects.create_user(username, **data)


def _make_superuser(username):
    return User.objects.create_superuser(
        username, f'{username}@example.com', 'pass',
        first_name='Admin', last_name='Super',
    )


def _grant(model, user, codename):
    ct = ContentType.objects.get_for_model(model)
    perm = ct.permission_set.get(codename=codename)
    user.user_permissions.add(perm)


class DashboardAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.url = reverse('dashboard:index')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_non_staff_non_client_forbidden(self):
        user = _make_user('plain')
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)


class DashboardContextTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.url = reverse('dashboard:index')

    def test_staff_can_access_and_gets_context_flags(self):
        staff = _make_user('staffdb', is_staff=True)
        self.client.force_login(staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context['title'], 'Dashboard')
        self.assertEqual(context['segment'], 'dashboard')
        self.assertEqual(context['selected_range'], '7d')
        self.assertFalse(context['is_client'])
        self.assertFalse(context['show_alerts'])
        self.assertFalse(context['show_forecast'])
        self.assertFalse(context['show_commercial'])

    def test_range_query_param(self):
        staff = _make_user('staffdb2', is_staff=True)
        self.client.force_login(staff)
        for rng in ('7d', '30d', '3m'):
            response = self.client.get(self.url, {'range': rng})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['selected_range'], rng)

    def test_permission_flags_enable_sections(self):
        staff = _make_user('staffdb3', is_staff=True)
        _grant(Warning, staff, 'view_warning')
        _grant(Forecasts, staff, 'view_forecast')
        _grant(ServiceSubscription, staff, 'view_subscription')
        self.client.force_login(staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertTrue(context['show_alerts'])
        self.assertTrue(context['show_forecast'])
        self.assertTrue(context['show_commercial'])

    def test_client_group_context(self):
        client = _make_user('clientdb')
        group = Group.objects.get_or_create(name='Clientes')[0]
        client.groups.add(group)
        Customer.objects.create(
            client_type='natural', user=client,
            account='1234567890123456', agency_bank='Banco Test',
            address='Calle 1', phone='12345678',
        )
        self.client.force_login(client)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertTrue(context['is_client'])
        self.assertFalse(context['show_commercial'])
        self.assertFalse(context['show_alerts'])
        self.assertFalse(context['show_forecast'])

    def test_client_with_data_sees_subs_and_invoices(self):
        client = _make_user('clientdb2')
        group = Group.objects.get_or_create(name='Clientes')[0]
        client.groups.add(group)
        customer = Customer.objects.create(
            client_type='natural', user=client,
            account='1234567890123456', agency_bank='Banco Test',
            address='Calle 1', phone='12345678',
        )
        admin = _make_superuser('adminsub')
        service = Service.objects.create(
            user=admin, title='Svc', summary='S',
            service_type='commercial', code='CDB1',
            price='50.00',
        )
        sub = ServiceSubscription.objects.create(
            customer=customer, service=service,
            payment_status='paid', start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
        )
        Invoice.objects.create(customer=customer, subscription=sub, number='INV-DB-1', amount='100.00')
        self.client.force_login(client)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context['client_active_subs'].count(), 1)
        self.assertEqual(context['client_invoices'].count(), 1)

    def test_superuser_gets_user_stats(self):
        _make_superuser('statsadmin')
        self.client.force_login(_make_superuser('statsadmin2'))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertIn('user_stats', context)
        self.assertIn('total_users', context['user_stats'])


class DashboardCommercialDataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.url = reverse('dashboard:index')
        cls.admin = _make_superuser('comadmin')
        _grant(ServiceSubscription, cls.admin, 'view_subscription')
        _grant(Invoice, cls.admin, 'view_invoice')
        customer = Customer.objects.create(
            client_type='natural', user=_make_user('comcust'),
            account='1234567890123456', agency_bank='Banco Test',
            address='Calle 1', phone='12345678',
        )
        service = Service.objects.create(
            user=cls.admin, title='Svc Com', summary='S',
            service_type='commercial', code='CDB2', price='50.00',
        )
        cls.sub = ServiceSubscription.objects.create(
            customer=customer, service=service,
            payment_status='paid', start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=60),
        )
        Invoice.objects.create(
            customer=customer, subscription=cls.sub,
            number='INV-DB-2', amount='150.00',
        )

    def test_income_chart_data_is_json(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context['selected_income_range'], '12m')
        json.loads(context['income_months'])
        billed = json.loads(context['income_billed_data'])
        paid = json.loads(context['income_paid_data'])
        self.assertEqual(len(billed), 12)
        self.assertEqual(len(paid), 12)

    def test_subscription_counts(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        context = response.context
        self.assertEqual(context['active_subs'], 1)
        self.assertEqual(context['expired_subs'], 0)
        self.assertEqual(context['pending_subs'], 0)
        self.assertIsInstance(context['month_income'], float)


class DashboardForecastChartTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.url = reverse('dashboard:index')
        cls.admin = _make_superuser('forecastadmin')
        _grant(Forecasts, cls.admin, 'view_forecast')
        cls.forecast = Forecasts.objects.create(
            date=timezone.now().date(),
            lp='Luna Nueva', nlp='Creciente',
            nlpd=timezone.now().date() + timezone.timedelta(days=7),
            sunrise=time(6, 30), sunset=time(19, 0),
            uv_index=8,
        )
        for region in ('north', 'interior', 'south'):
            ForecastRegions.objects.create(
                forecast=cls.forecast, region=region,
                period='afternoon', temp=30,
                weather='PN', wind_dir='NE', wind_speed='10',
            )
            ForecastRegions.objects.create(
                forecast=cls.forecast, region=region,
                period='night', temp=24,
                weather='PN', wind_dir='NE', wind_speed='8',
            )

    def test_forecast_chart_data(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertTrue(context['has_forecasts'])
        self.assertEqual(json.loads(context['temperature_labels']), [self.forecast.date.strftime('%d/%m')])
        self.assertEqual(json.loads(context['max_temperatures_north']), [30.0])
        self.assertEqual(json.loads(context['min_temperatures_north']), [24.0])
        self.assertEqual(json.loads(context['max_temperatures_south']), [30.0])
        self.assertEqual(json.loads(context['max_temperatures_inland']), [30.0])
        self.assertIsNotNone(context['latest_forecast'])
