from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from unittest.mock import patch
from django.urls import reverse
from django.utils import timezone

from apps.commercial.models import (
    Certificate,
    Contract,
    Customer,
    Invoice,
    Service,
    ServiceSubscription,
)
from apps.core.models import SiteConfiguration


def _make_user(username='testuser', **kwargs):
    data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': f'{username}@example.com',
    }
    data.update(kwargs)
    return User.objects.create_user(username, **data)


def _make_superuser(username, **kwargs):
    email = kwargs.pop('email', f'{username}@example.com')
    data = {
        'first_name': 'Admin',
        'last_name': 'Super',
    }
    data.update(kwargs)
    return User.objects.create_superuser(username, email, 'pass', **data)


def disable_maintenance_mode():
    SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})


class CustomerListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.staff_user = _make_user('staff', is_staff=True)
        cls.url = reverse('commercial:cliente_list')

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/accounts/login/?next={self.url}')

    def test_user_with_permission_can_access(self):
        ct = ContentType.objects.get_for_model(Customer)
        perm = ct.permission_set.get(codename='view_customer')
        self.staff_user.user_permissions.add(perm)
        self.client.force_login(self.staff_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class CustomerCreateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.admin = _make_superuser('admin')
        cls.url = reverse('commercial:cliente_create')

    def test_get_returns_200(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_creates_customer_and_user(self):
        self.client.force_login(self.admin)
        data = {
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
            'address': 'Calle 123',
            'phone': '12345678',
        }
        self.client.post(self.url, data, follow=True)
        self.assertTrue(Customer.objects.filter(company_name='Empresa SL').exists())
        self.assertTrue(User.objects.filter(username='newcliente').exists())


class CustomerUpdateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.admin = _make_superuser('admin2')
        cls.owner_user = _make_user('owner')
        cls.other_user = _make_user('other')
        # Use juridica customer with all fields filled to avoid
        # CheckUserProfileMiddleware crash on None fields
        cls.customer = Customer.objects.create(
            client_type='juridica',
            user=cls.owner_user,
            company_name='Test Corp',
            reeup='111.1.1111',
            nit='11111111111',
            account='1234567890123456',
            agency_bank='Banco Test',
            address='Original',
            phone='12345678',
        )
        # Give owner the change_customer permission
        ct = ContentType.objects.get_for_model(Customer)
        perm = ct.permission_set.get(codename='change_customer')
        cls.owner_user.user_permissions.add(perm)

    def test_owner_can_access(self):
        self.client.force_login(self.owner_user)
        url = reverse('commercial:cliente_update', args=[self.customer.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_superuser_can_access(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:cliente_update', args=[self.customer.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_access(self):
        self.client.force_login(self.other_user)
        url = reverse('commercial:cliente_update', args=[self.customer.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)


class CustomerDeleteViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.staff_user = _make_user('staffdel', is_staff=True)
        cls.customer = Customer.objects.create(
            client_type='natural',
            user=_make_user('todel'),
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )

    def test_post_soft_deletes(self):
        ct = ContentType.objects.get_for_model(Customer)
        perm = ct.permission_set.get(codename='delete_customer')
        self.staff_user.user_permissions.add(perm)
        self.client.force_login(self.staff_user)
        url = reverse('commercial:cliente_delete', args=[self.customer.uuid])
        self.client.post(url, follow=True)
        self.customer.refresh_from_db()
        self.assertFalse(self.customer.record_active)


class CustomerHardDeleteViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.admin = _make_superuser('admin3')
        cls.normal = _make_user('normal')
        cls.customer = Customer.objects.create(
            client_type='natural',
            user=_make_user('harddelcust'),
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )

    def test_superuser_can_hard_delete(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:cliente_hard_delete', args=[self.customer.uuid])
        pk = self.customer.pk
        self.client.post(url, follow=True)
        self.assertFalse(Customer.objects.filter(pk=pk).exists())

    def test_hard_delete_with_own_user_does_not_crash(self):
        own = _make_superuser('ownadmin')
        own_customer = Customer.objects.create(
            client_type='natural',
            user=own,
            address='Addr2',
            phone='87654321',
            account='8923456789012345',
            agency_bank='BANDEC',
        )
        self.client.force_login(own)
        url = reverse('commercial:cliente_hard_delete', args=[own_customer.uuid])
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Customer.objects.filter(pk=own_customer.pk).exists())
        self.assertTrue(own.__class__.objects.filter(pk=own.pk).exists())

    def test_normal_user_cannot_hard_delete(self):
        self.client.force_login(self.normal)
        url = reverse('commercial:cliente_hard_delete', args=[self.customer.uuid])
        self.client.post(url, follow=True)
        # Normal user cannot hard delete (customer still exists)
        self.assertTrue(Customer.objects.filter(pk=self.customer.pk).exists())


class ServiceListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.staff = _make_user('staffsvc', is_staff=True)
        cls.url = reverse('commercial:servicio_list')

    def test_staff_can_access(self):
        ct = ContentType.objects.get_for_model(Service)
        perm = ct.permission_set.get(codename='view_service')
        self.staff.user_permissions.add(perm)
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_non_staff_denied(self):
        user = _make_user('normalsvc')
        ct = ContentType.objects.get_for_model(Service)
        perm = ct.permission_set.get(codename='view_service')
        user.user_permissions.add(perm)
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)


class ServiceCreateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.admin = _make_superuser('admin4')
        cls.url = reverse('commercial:servicio_create')

    def test_post_creates_service(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile(
            'doc.pdf',
            b'PDF content',
            content_type='application/pdf',
        )
        data = {
            'title': 'New Service',
            'summary': 'Test summary',
            'service_type': 'public',
            'pdf': pdf,
        }
        self.client.post(self.url, data, follow=True)
        self.assertTrue(Service.objects.filter(title='New Service').exists())


class ServiceDeleteViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.admin = _make_superuser('admin5')
        cls.service = Service.objects.create(
            user=cls.admin,
            title='To Delete',
            summary='Del',
            service_type='public',
        )

    def test_post_soft_deletes(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:servicio_delete', args=[self.service.uuid])
        self.client.post(url, follow=True)
        self.service.refresh_from_db()
        self.assertFalse(self.service.record_active)


class SubscriptionListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.staff = _make_user('staffsub', is_staff=True)
        cls.url = reverse('commercial:suscripcion_list')

    def test_staff_can_access(self):
        ct = ContentType.objects.get_for_model(ServiceSubscription)
        perm = ct.permission_set.get(codename='view_subscription')
        self.staff.user_permissions.add(perm)
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class InvoiceListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.user = _make_user('staffinv', is_staff=True)
        cls.url = reverse('commercial:factura_list')

    def test_staff_can_access(self):
        ct = ContentType.objects.get_for_model(Invoice)
        perm = ct.permission_set.get(codename='view_invoice')
        self.user.user_permissions.add(perm)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class CancelInvoiceViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.admin = _make_superuser('admin6')
        customer = Customer.objects.create(
            client_type='natural',
            user=_make_user('cancust'),
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )
        cls.invoice = Invoice.objects.create(
            customer=customer,
            number='INV-CAN',
            amount=Decimal('100.00'),
        )

    def test_post_cancels_invoice(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:factura_cancel', args=[self.invoice.uuid])
        self.client.post(url, follow=True)
        self.invoice.refresh_from_db()
        self.assertTrue(self.invoice.is_cancelled)

    @patch('apps.commercial.views.invoice_utils.generate_invoice_pdf_standalone')
    def test_download_generates_pdf_if_missing(self, mock_gen):
        def _fake_gen(invoice, customer, start, end, reg, items):
            invoice.pdf.save('factura_test.pdf', ContentFile(b'%PDF-1.4 test'))

        mock_gen.side_effect = _fake_gen
        self.client.force_login(self.admin)
        url = reverse('commercial:factura_download', args=[self.invoice.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertEqual(b''.join(response.streaming_content), b'%PDF-1.4 test')
        # Se generó bajo demanda porque el PDF no existía.
        mock_gen.assert_called_once()


class ContractListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.user = _make_user('staffcon', is_staff=True)
        cls.url = reverse('commercial:contrato_list')

    def test_staff_can_access(self):
        ct = ContentType.objects.get_for_model(Contract)
        perm = ct.permission_set.get(codename='view_contract')
        self.user.user_permissions.add(perm)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class ContractCreateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.admin = _make_superuser('admin7')
        customer = Customer.objects.create(
            client_type='natural',
            user=_make_user('conccust'),
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )
        service = Service.objects.create(
            user=cls.admin,
            title='Svc',
            summary='Svc',
            service_type='commercial',
            code='C100',
            price=Decimal('50.00'),
        )
        cls.sub = ServiceSubscription.objects.create(
            customer=customer,
            service=service,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )
        cls.url = reverse('commercial:contrato_create')

    def test_post_creates_contract(self):
        self.client.force_login(self.admin)
        data = {
            'subscription': self.sub.pk,
            'number': 'CONT-001',
            'date': date.today().isoformat(),
            'commercial_registry': 'REG-001',
        }
        self.client.post(self.url, data, follow=True)
        self.assertTrue(Contract.objects.filter(number='CONT-001').exists())

    def test_invalid_post_repopulates_values(self):
        self.client.force_login(self.admin)
        data = {
            'number': 'CONT-002',
            'date': date.today().isoformat(),
            'commercial_registry': 'REG-002',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="CONT-002"')
        self.assertContains(response, f'value="{date.today().strftime("%d/%m/%Y")}"')
        self.assertContains(response, 'value="REG-002"')


class ContractDeleteViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.admin = _make_superuser('admin8')
        customer = Customer.objects.create(
            client_type='natural',
            user=_make_user('delcust'),
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )
        service = Service.objects.create(
            user=cls.admin,
            title='Svc2',
            summary='Svc2',
            service_type='commercial',
            code='C101',
            price=Decimal('60.00'),
        )
        sub = ServiceSubscription.objects.create(
            customer=customer,
            service=service,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )
        cls.contract = Contract.objects.create(
            subscription=sub,
            number='CONT-DEL',
            date=date.today(),
            commercial_registry='REG-DEL',
        )

    def test_post_soft_deletes(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:contrato_delete', args=[self.contract.uuid])
        self.client.post(url, follow=True)
        self.contract.refresh_from_db()
        self.assertFalse(self.contract.record_active)


class CertificateListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.user = _make_user('staffcert', is_staff=True)
        cls.url = reverse('commercial:certificado_list')

    def test_staff_can_access(self):
        ct = ContentType.objects.get_for_model(Certificate)
        perm = ct.permission_set.get(codename='view_certificate')
        self.user.user_permissions.add(perm)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class CertificateDeleteViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.admin = _make_superuser('admin9')
        customer = Customer.objects.create(
            client_type='natural',
            user=_make_user('certcust'),
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )
        service = Service.objects.create(
            user=cls.admin,
            title='Svc3',
            summary='Svc3',
            service_type='commercial',
            code='C102',
            price=Decimal('70.00'),
        )
        sub = ServiceSubscription.objects.create(
            customer=customer,
            service=service,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )
        pdf = SimpleUploadedFile(
            'cert.pdf',
            b'PDF',
            content_type='application/pdf',
        )
        cls.cert = Certificate.objects.create(
            subscription=sub,
            pdf=pdf,
        )

    def test_post_soft_deletes(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:certificado_delete', args=[self.cert.uuid])
        self.client.post(url, follow=True)
        self.cert.refresh_from_db()
        self.assertFalse(self.cert.record_active)


class CSVExportViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.admin = _make_superuser('admin10')

    def test_customer_csv(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:cliente_export_csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Content-Type'),
            'text/csv; charset=utf-8',
        )
        content = response.content.decode('utf-8-sig')
        self.assertIn('Tipo de Cliente', content)
        self.assertIn('Agencia Bancaria', content)

    def test_service_csv(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:servicio_export_csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8-sig')
        self.assertIn('Fecha', content)
        self.assertIn('Suscripciones', content)

    def test_invoice_csv(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:factura_export_csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8-sig')
        self.assertIn('Servicio(s)', content)
        self.assertIn('Estado', content)

    def test_subscription_csv(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:suscripcion_export_csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8-sig')
        self.assertIn('Método de Pago', content)

    def test_contract_csv(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:contrato_export_csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_certificate_csv(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:certificado_export_csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
