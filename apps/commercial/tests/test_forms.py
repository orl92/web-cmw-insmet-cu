import struct
import zlib
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from apps.commercial.forms.certificate import CertificateForm
from apps.commercial.forms.contract import ContractForm
from apps.commercial.forms.customer import (
    CustomerForm,
    CustomerForUserForm,
    CustomerUpdateForm,
)
from apps.commercial.forms.invoice import InvoiceForm
from apps.commercial.forms.service import ServiceForm
from apps.commercial.forms.subscription import (
    PaymentMethodForm,
    SubscriptionForm,
)
from apps.commercial.models import (
    Customer,
    Service,
    ServiceSubscription,
)


def _make_png():
    """Generate a minimal valid PNG in memory."""
    width, height = 1, 1
    raw = b'\x00' + b'\xff\x00\x00\x00' * width * height

    def chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)

    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    return (
        b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', ihdr)
        + chunk(b'IDAT', zlib.compress(raw))
        + chunk(b'IEND', b'')
    )


def _make_user(username='testuser', **kwargs):
    data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': f'{username}@example.com',
    }
    data.update(kwargs)
    return User.objects.create_user(username, **data)


class CustomerFormTests(TestCase):
    def _valid_juridica_data(self):
        return {
            'username': 'newcliente',
            'password': 'Pass1234!',
            'password2': 'Pass1234!',
            'email': 'cliente@example.com',
            'client_type': 'juridica',
            'company_name': 'Empresa SL',
            'reeup': '123.4.5678',
            'nit': '12345678901',
            'account': '1234567890123456',
            'agency_bank': 'Banco Test',
            'address': 'Calle Principal 123',
            'phone': '12345678',
        }

    def test_valid_juridica_form(self):
        form = CustomerForm(data=self._valid_juridica_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_password_mismatch(self):
        data = self._valid_juridica_data()
        data['password2'] = 'DifferentPass1!'
        form = CustomerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_juridica_requires_company_fields(self):
        data = self._valid_juridica_data()
        data['company_name'] = ''
        data['reeup'] = ''
        data['nit'] = ''
        form = CustomerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('company_name', form.errors)
        self.assertIn('reeup', form.errors)
        self.assertIn('nit', form.errors)

    def test_natural_does_not_require_company_fields(self):
        data = self._valid_juridica_data()
        data['client_type'] = 'natural'
        data['company_name'] = ''
        data['reeup'] = ''
        data['nit'] = ''
        form = CustomerForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_reeup_format(self):
        data = self._valid_juridica_data()
        data['reeup'] = '12345'
        form = CustomerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('reeup', form.errors)

    def test_invalid_nit_format(self):
        data = self._valid_juridica_data()
        data['nit'] = '123'
        form = CustomerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nit', form.errors)

    def test_invalid_account_format(self):
        data = self._valid_juridica_data()
        data['account'] = '123'
        form = CustomerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('account', form.errors)

    def test_invalid_phone_format(self):
        data = self._valid_juridica_data()
        data['phone'] = 'abc'
        form = CustomerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_multi_phone_format(self):
        data = self._valid_juridica_data()
        data['phone'] = '51234567, 32270000-12345678; 55556666'
        form = CustomerForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_multi_phone_has_bad_part(self):
        data = self._valid_juridica_data()
        data['phone'] = '51234567, 32270'
        form = CustomerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_save_creates_user_and_customer(self):
        data = self._valid_juridica_data()
        form = CustomerForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        customer = form.save()
        self.assertIsNotNone(customer.pk)
        self.assertIsNotNone(customer.user)
        self.assertTrue(User.objects.filter(username='newcliente').exists())
        self.assertEqual(customer.user.email, 'cliente@example.com')

    def test_unique_reeup(self):
        user1 = _make_user('u1')
        Customer.objects.create(
            client_type='juridica',
            user=user1,
            company_name='Existing',
            reeup='123.4.5678',
            nit='11111111111',
            account='1111111111111111',
            address='Addr',
            phone='11111111',
        )
        data = self._valid_juridica_data()
        data['username'] = 'newuser2'
        data['email'] = 'u2@example.com'
        data['nit'] = '22222222222'
        data['account'] = '2222222222222222'
        form = CustomerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('reeup', form.errors)

    def test_unique_nit(self):
        user1 = _make_user('u1')
        Customer.objects.create(
            client_type='juridica',
            user=user1,
            company_name='Existing',
            reeup='111.1.1111',
            nit='11111111111',
            account='1111111111111111',
            address='Addr',
            phone='11111111',
        )
        data = self._valid_juridica_data()
        data['nit'] = '11111111111'
        data['username'] = 'newuser2'
        data['email'] = 'u2@example.com'
        data['reeup'] = '222.2.2222'
        data['account'] = '2222222222222222'
        form = CustomerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nit', form.errors)


class CustomerUpdateFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('updateuser')
        cls.customer = Customer.objects.create(
            client_type='juridica',
            user=cls.user,
            company_name='Old Name',
            reeup='111.1.1111',
            nit='11111111111',
            account='1111111111111111',
            address='Old address',
            phone='11111111',
        )

    def test_valid_update(self):
        form = CustomerUpdateForm(
            instance=self.customer,
            data={
                'client_type': 'juridica',
                'company_name': 'New Name',
                'reeup': '111.1.1111',
                'nit': '11111111111',
                'account': '1111111111111111',
                'agency_bank': 'New Bank',
                'address': 'New address',
                'phone': '11111111',
                'email': 'updated@example.com',
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        customer = form.save()
        self.assertEqual(customer.company_name, 'New Name')
        self.assertEqual(customer.user.email, 'updated@example.com')


class CustomerForUserFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('foruser')

    def test_valid_form(self):
        form = CustomerForUserForm(
            user=self.user,
            data={
                'client_type': 'natural',
                'account': '1234567890123456',
                'agency_bank': 'Banco Test',
                'address': 'Addr',
                'phone': '12345678',
                'email': 'foruser@example.com',
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        customer = form.save()
        self.assertEqual(customer.user, self.user)
        self.assertEqual(customer.user.email, 'foruser@example.com')


class ServiceFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('svcform')

    def test_public_service_valid(self):
        pdf = SimpleUploadedFile(
            'doc.pdf',
            b'PDF',
            content_type='application/pdf',
        )
        form = ServiceForm(
            user=self.user,
            data={
                'title': 'Public Svc',
                'summary': 'A public service',
                'service_type': 'public',
            },
            files={'pdf': pdf},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_public_service_rejects_image(self):
        pdf = SimpleUploadedFile(
            'doc.pdf',
            b'PDF',
            content_type='application/pdf',
        )
        image = SimpleUploadedFile(
            'img.png',
            b'PNG',
            content_type='image/png',
        )
        form = ServiceForm(
            user=self.user,
            data={
                'title': 'Bad Public',
                'summary': 'Should fail',
                'service_type': 'public',
            },
            files={'pdf': pdf, 'image': image},
        )
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

    def test_public_service_requires_pdf(self):
        form = ServiceForm(
            user=self.user,
            data={
                'title': 'No PDF',
                'summary': 'Should fail',
                'service_type': 'public',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn('pdf', form.errors)

    def test_commercial_service_valid(self):
        image = SimpleUploadedFile(
            'img.png',
            _make_png(),
            content_type='image/png',
        )
        form = ServiceForm(
            user=self.user,
            data={
                'title': 'Comm Svc',
                'summary': 'A commercial service',
                'service_type': 'commercial',
                'code': 'C001',
                'price': '100.00',
            },
            files={'image': image},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_commercial_service_requires_code(self):
        image = SimpleUploadedFile(
            'img.png',
            b'PNG',
            content_type='image/png',
        )
        form = ServiceForm(
            user=self.user,
            data={
                'title': 'No Code',
                'summary': 'Should fail',
                'service_type': 'commercial',
            },
            files={'image': image},
        )
        self.assertFalse(form.is_valid())
        self.assertIn('code', form.errors)

    def test_commercial_service_requires_price(self):
        image = SimpleUploadedFile(
            'img.png',
            b'PNG',
            content_type='image/png',
        )
        form = ServiceForm(
            user=self.user,
            data={
                'title': 'No Price',
                'summary': 'Should fail',
                'service_type': 'commercial',
                'code': 'C002',
            },
            files={'image': image},
        )
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)

    def test_commercial_service_rejects_pdf(self):
        pdf = SimpleUploadedFile(
            'doc.pdf',
            b'PDF',
            content_type='application/pdf',
        )
        image = SimpleUploadedFile(
            'img.png',
            b'PNG',
            content_type='image/png',
        )
        form = ServiceForm(
            user=self.user,
            data={
                'title': 'Bad Comm',
                'summary': 'Should fail',
                'service_type': 'commercial',
                'code': 'C003',
                'price': '50.00',
            },
            files={'image': image, 'pdf': pdf},
        )
        self.assertFalse(form.is_valid())
        self.assertIn('pdf', form.errors)


class SubscriptionFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('subform')
        cls.customer = Customer.objects.create(
            client_type='natural',
            user=cls.user,
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )
        cls.service = Service.objects.create(
            user=cls.user,
            title='Comm Svc',
            summary='Commercial',
            service_type='commercial',
            code='C010',
            price=Decimal('60.00'),
        )

    def test_period_1m_calculates_end_date(self):
        form = SubscriptionForm(
            data={
                'customer': self.customer.pk,
                'service': self.service.pk,
                'period': '1m',
                'payment_status': 'requested',
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        sub = form.save(commit=False)
        self.assertIsNotNone(sub.start_date)
        self.assertIsNotNone(sub.end_date)
        delta = (sub.end_date - sub.start_date).days
        self.assertEqual(delta, 30)

    def test_period_3m_calculates_end_date(self):
        form = SubscriptionForm(
            data={
                'customer': self.customer.pk,
                'service': self.service.pk,
                'period': '3m',
                'payment_status': 'requested',
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        sub = form.save(commit=False)
        delta = (sub.end_date - sub.start_date).days
        self.assertEqual(delta, 90)

    def test_period_1y_calculates_end_date(self):
        form = SubscriptionForm(
            data={
                'customer': self.customer.pk,
                'service': self.service.pk,
                'period': '1y',
                'payment_status': 'requested',
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        sub = form.save(commit=False)
        delta = (sub.end_date - sub.start_date).days
        self.assertEqual(delta, 365)

    def test_custom_period_validates_dates(self):
        start = timezone.now()
        end = start - timedelta(days=1)
        form = SubscriptionForm(
            data={
                'customer': self.customer.pk,
                'service': self.service.pk,
                'period': 'custom',
                'payment_status': 'requested',
                'start_date': start.strftime('%Y-%m-%dT%H:%M'),
                'end_date': end.strftime('%Y-%m-%dT%H:%M'),
            }
        )
        self.assertFalse(form.is_valid())

    def test_tempus_datetime_format_parses(self):
        form = SubscriptionForm(
            data={
                'customer': self.customer.pk,
                'service': self.service.pk,
                'period': 'custom',
                'payment_status': 'requested',
                'start_date': '23/08/2026 06:30 PM',
                'end_date': '23/09/2026 11:45 AM',
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data['start_date'].strftime('%Y-%m-%d %H:%M'),
            '2026-08-23 18:30',
        )
        self.assertEqual(
            form.cleaned_data['end_date'].strftime('%Y-%m-%d %H:%M'),
            '2026-09-23 11:45',
        )


class ContractFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('conform')
        customer = Customer.objects.create(
            client_type='natural',
            user=cls.user,
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )
        service = Service.objects.create(
            user=cls.user,
            title='Svc',
            summary='Svc',
            service_type='commercial',
            code='C020',
            price=Decimal('70.00'),
        )
        cls.sub = ServiceSubscription.objects.create(
            customer=customer,
            service=service,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )

    def test_valid_contract_form(self):
        form = ContractForm(
            data={
                'subscription': self.sub.pk,
                'number': 'CONT-001',
                'date': date.today().isoformat(),
                'commercial_registry': 'REG-001',
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_contract_saves(self):
        form = ContractForm(
            data={
                'subscription': self.sub.pk,
                'number': 'CONT-002',
                'date': date.today().isoformat(),
                'commercial_registry': 'REG-002',
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        contract = form.save()
        self.assertIsNotNone(contract.pk)


class CertificateFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('certform')
        customer = Customer.objects.create(
            client_type='natural',
            user=cls.user,
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )
        service = Service.objects.create(
            user=cls.user,
            title='Svc',
            summary='Svc',
            service_type='commercial',
            code='C030',
            price=Decimal('80.00'),
        )
        cls.sub = ServiceSubscription.objects.create(
            customer=customer,
            service=service,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )

    def test_valid_certificate_form(self):
        pdf = SimpleUploadedFile(
            'cert.pdf',
            b'PDF',
            content_type='application/pdf',
        )
        form = CertificateForm(
            data={'subscription': self.sub.pk},
            files={'pdf': pdf},
        )
        self.assertTrue(form.is_valid(), form.errors)


class PaymentMethodFormTests(TestCase):
    def test_valid_form(self):
        form = PaymentMethodForm(
            data={
                'payment_method': 'qr',
                'start_date': date.today().isoformat(),
                'end_date': (date.today() + timedelta(days=30)).isoformat(),
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_requires_dates(self):
        form = PaymentMethodForm(data={'payment_method': 'transfer'})
        self.assertFalse(form.is_valid())
        self.assertIn('start_date', form.errors)
        self.assertIn('end_date', form.errors)


class InvoiceFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('invform')
        cls.customer = Customer.objects.create(
            client_type='natural',
            user=cls.user,
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )

    def test_invoice_form_requires_customer(self):
        form = InvoiceForm(
            data={
                'start_date': date.today().isoformat(),
                'end_date': (date.today() + timedelta(days=30)).isoformat(),
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('customer', form.errors)
