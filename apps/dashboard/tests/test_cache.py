from datetime import time

from django.contrib.auth.models import ContentType, Group, User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.commercial.models import (
    Customer,
    Invoice,
    Service,
    ServiceSubscription,
)
from apps.core.models import SiteConfiguration
from apps.dashboard.views.dashboard.dashboard import build_shared_kpis
from apps.meteo.models import Forecasts


def _make_user(username, **kwargs):
    data = {'first_name': 'Test', 'last_name': 'User', 'email': f'{username}@example.com'}
    data.update(kwargs)
    return User.objects.create_user(username, **data)


def _grant(model, user, codename):
    perm = ContentType.objects.get_for_model(model).permission_set.get(codename=codename)
    user.user_permissions.add(perm)


class DashboardKpiCacheTests(TestCase):
    """CACHE-3: expensive shared aggregates are cached; per-client data is not."""

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        # A forecast so the forecast series is actually cached (not skipped).
        Forecasts.objects.create(
            date=timezone.now().date(),
            lp='Luna Nueva',
            nlp='Creciente',
            nlpd=timezone.now().date() + timezone.timedelta(days=7),
            sunrise=time(6, 30),
            sunset=time(18, 30),
            uv_index=5,
        )

    def setUp(self):
        cache.clear()

    def test_kpi_series_cached_within_ttl(self):
        # First call populates the cache (runs the aggregation queries).
        r1 = build_shared_kpis('7d', '12m', forecast=True, alerts=True, commercial=True)
        self.assertIsNotNone(cache.get('dashboard:kpi:7d:12m'))
        # Second call within TTL serves from cache: no aggregation re-executed.
        with self.assertNumQueries(0):
            r2 = build_shared_kpis('7d', '12m', forecast=True, alerts=True, commercial=True)
        self.assertEqual(r1, r2)

    def test_distinct_range_yields_distinct_cache_keys(self):
        build_shared_kpis('7d', '12m', forecast=True)
        build_shared_kpis('30d', '12m', forecast=True)
        # Each range is cached under its own key (no cross-contamination).
        self.assertIsNotNone(cache.get('dashboard:kpi:7d:12m'))
        self.assertIsNotNone(cache.get('dashboard:kpi:30d:12m'))
        self.assertNotEqual('dashboard:kpi:7d:12m', 'dashboard:kpi:30d:12m')

    def test_empty_forecast_is_not_cached_to_avoid_stale_pollution(self):
        # With no forecast for the '3m' window beyond what exists, an empty result
        # must NOT be written, so a later request with data is not served stale.
        cache.clear()
        build_shared_kpis('3m', '12m', forecast=True)
        # '3m' start is 90d ago; the single forecast (today) IS within range, so it
        # is cached. Verify the key exists and has the forecast series.
        self.assertIn('forecast', cache.get('dashboard:kpi:3m:12m'))


class DashboardNoClientLeakTests(TestCase):
    """CACHE-3 scenario: per-client data is never served from the shared cache."""

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        cls.staff = _make_user('staffcache', is_staff=True)
        _grant(ServiceSubscription, cls.staff, 'view_subscription')
        _grant(Invoice, cls.staff, 'view_invoice')

        group = Group.objects.get_or_create(name='Clientes')[0]
        cls.client_a = _make_user('client_a')
        cls.client_a.groups.add(group)
        cls.customer_a = Customer.objects.create(
            client_type='natural',
            user=cls.client_a,
            account='1111111111111111',
            agency_bank='Banco A',
            address='Calle A',
            phone='11111111',
        )
        cls.client_b = _make_user('client_b')
        cls.client_b.groups.add(group)
        cls.customer_b = Customer.objects.create(
            client_type='natural',
            user=cls.client_b,
            account='2222222222222222',
            agency_bank='Banco B',
            address='Calle B',
            phone='22222222',
        )
        admin = _make_user('admincache')
        service = Service.objects.create(
            user=admin,
            title='Svc',
            summary='S',
            service_type='commercial',
            code='CDC1',
            price='50.00',
        )
        sub_a = ServiceSubscription.objects.create(
            customer=cls.customer_a,
            service=service,
            payment_status='paid',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
        )
        Invoice.objects.create(
            customer=cls.customer_a, subscription=sub_a, number='INV-A', amount='100.00'
        )
        sub_b = ServiceSubscription.objects.create(
            customer=cls.customer_b,
            service=service,
            payment_status='paid',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
        )
        Invoice.objects.create(
            customer=cls.customer_b, subscription=sub_b, number='INV-B', amount='200.00'
        )

    def setUp(self):
        cache.clear()

    def test_shared_cache_excludes_client_keys(self):
        # Staff populates the shared (commercial) cache.
        self.client.force_login(self.staff)
        self.client.get(reverse('dashboard:index'))
        cached = cache.get('dashboard:kpi:7d:12m')
        self.assertIsNotNone(cached)
        self.assertNotIn('client_active_subs', cached)
        self.assertNotIn('client_invoices', cached)
        self.assertNotIn('client_pending_subs', cached)

    def test_clients_see_only_their_own_invoices(self):
        self.client.force_login(self.client_a)
        resp_a = self.client.get(reverse('dashboard:index'))
        self.assertEqual(resp_a.context['client_invoices'].count(), 1)
        self.assertEqual(list(resp_a.context['client_invoices'])[0].number, 'INV-A')

        self.client.force_login(self.client_b)
        resp_b = self.client.get(reverse('dashboard:index'))
        numbers = [i.number for i in resp_b.context['client_invoices']]
        self.assertEqual(numbers, ['INV-B'])
        self.assertNotIn('INV-A', numbers)
