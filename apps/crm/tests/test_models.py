from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.crm.models import Customer, Service, ServiceSubscription


class CustomerModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('cust', 'cust@example.com', 'password')

    def test_create_customer(self):
        c = Customer.objects.create(
            company_name='Test Corp', reeup='123.1.1234', nit='12345678901',
            account='1234567890123456', agency_bank='Test Bank',
            address='Addr', user=self.user, phone='12345678', accept_terms=True,
        )
        self.assertEqual(str(c), 'Test Corp')
        self.assertIsNotNone(c.uuid)

    def test_invalid_reeup_raises_error(self):
        c = Customer(
            company_name='Test', reeup='invalid', nit='12345678901',
            account='1234567890123456', address='Addr',
            user=self.user, phone='12345678',
        )
        with self.assertRaises(ValidationError):
            c.full_clean()


class ServiceModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('svc', 'svc@example.com', 'password')

    def test_create_service(self):
        s = Service.objects.create(title='Test Svc', summary='Sum', user=self.user, service_type='public')
        self.assertEqual(str(s), 'Test Svc')
        self.assertIsNotNone(s.uuid)

    def test_get_image_url_default(self):
        s = Service.objects.create(title='Svc', summary='S', user=self.user)
        self.assertIn('default.svg', s.get_image_url())


class ServiceSubscriptionModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('sub', 'sub@example.com', 'password')
        cls.customer = Customer.objects.create(
            company_name='Sub Corp', reeup='111.1.1111', nit='11111111111',
            account='1111111111111111', address='Addr',
            user=cls.user, phone='11111111')
        cls.service = Service.objects.create(title='Sub Svc', summary='S', user=cls.user)

    def test_soft_delete(self):
        sub = ServiceSubscription.objects.create(customer=self.customer, service=self.service)
        sub.delete()
        self.assertFalse(sub.record_active)
        self.assertIsNotNone(sub.deleted_at)

    def test_hard_delete(self):
        sub = ServiceSubscription.objects.create(customer=self.customer, service=self.service)
        pk = sub.pk
        sub.hard_delete()
        self.assertFalse(ServiceSubscription.objects.filter(pk=pk).exists())

    def test_is_active(self):
        future = timezone.now() + timedelta(days=30)
        sub = ServiceSubscription.objects.create(
            customer=self.customer, service=self.service,
            payment_status='paid', end_date=future)
        self.assertTrue(sub.is_active)

    def test_is_active_expired(self):
        past = timezone.now() - timedelta(days=1)
        sub = ServiceSubscription.objects.create(
            customer=self.customer, service=self.service,
            payment_status='paid', end_date=past)
        self.assertFalse(sub.is_active)

    def test_clean_start_before_end(self):
        sub = ServiceSubscription(
            customer=self.customer, service=self.service,
            start_date=timezone.now() + timedelta(days=5),
            end_date=timezone.now(),
        )
        with self.assertRaises(ValidationError):
            sub.full_clean()
