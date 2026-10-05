import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.commercial.models import (
    Certificate,
    Customer,
    Invoice,
    Service,
    ServiceSubscription,
)
from apps.commercial.tests.factories import natural_customer
from apps.core.models import SiteConfiguration


def _disable_maintenance():
    SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})


def _make_user(username='testuser', is_staff=False, **kwargs):
    defaults = {
        'first_name': 'Test',
        'last_name': 'User',
    }
    defaults.update(kwargs)
    return User.objects.create_user(
        username,
        email=f'{username}@example.com',
        password='testpass123',
        is_staff=is_staff,
        **defaults,
    )


def _make_superuser(username='admin'):
    return User.objects.create_superuser(
        username,
        f'{username}@example.com',
        'adminpass',
        first_name='Admin',
        last_name='Super',
    )


def _add_perm(user, model, codename):
    ct = ContentType.objects.get_for_model(model)
    perm = ct.permission_set.get(codename=codename)
    user.user_permissions.add(perm)


class BulkExportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_superuser('bulkadmin')
        cls.customer = natural_customer(
            _make_user('bulexpcust'),
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )
        cls.service = Service.objects.create(
            user=cls.admin,
            title='Bulk Export Service',
            summary='Test',
            service_type='commercial',
            code='BEX01',
            price=Decimal('50.00'),
        )
        cls.sub = ServiceSubscription.objects.create(
            customer=cls.customer,
            service=cls.service,
        )

    def test_customer_bulk_export_returns_selected_rows(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:cliente_bulk')
        data = {
            'action': 'export',
            'uuids': [str(self.customer.uuid)],
        }
        resp = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/csv; charset=utf-8')
        content = resp.content.decode('utf-8-sig')
        self.assertIn('Tipo de Cliente', content)
        self.assertIn('bulexpcust', content)

    def test_subscription_bulk_export_returns_selected_rows(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:suscripcion_bulk')
        data = {
            'action': 'export',
            'uuids': [str(self.sub.uuid)],
        }
        resp = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8-sig')
        self.assertIn('Servicio', content)
        self.assertIn('Bulk Export Service', content)

    def test_invoice_bulk_export_returns_selected_rows(self):
        invoice = Invoice.objects.create(
            customer=self.customer,
            number='BULK-INV-001',
            amount=Decimal('100.00'),
        )
        self.client.force_login(self.admin)
        url = reverse('commercial:factura_bulk')
        data = {
            'action': 'export',
            'uuids': [str(invoice.uuid)],
        }
        resp = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8-sig')
        self.assertIn('Número', content)
        self.assertIn('BULK-INV-001', content)


class BulkDeleteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_superuser('bulkdeladmin')
        cls.customer1 = natural_customer(
            _make_user('bulkdel1'),
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )
        cls.customer2 = natural_customer(
            _make_user('bulkdel2'),
            address='Addr2',
            phone='87654321',
            account='9876543210987654',
        )

    def test_bulk_delete_soft_deletes_records(self):
        self.client.force_login(self.admin)
        _add_perm(self.admin, Customer, 'delete_customer')
        url = reverse('commercial:cliente_bulk')
        data = {
            'action': 'delete',
            'uuids': [str(self.customer1.uuid), str(self.customer2.uuid)],
        }
        resp = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body['processed'], 2)
        self.assertEqual(body['skipped'], 0)

        self.customer1.refresh_from_db()
        self.customer2.refresh_from_db()
        self.assertFalse(self.customer1.record_active)
        self.assertFalse(self.customer2.record_active)
        self.assertIsNotNone(self.customer1.deleted_at)
        self.assertIsNotNone(self.customer2.deleted_at)
        # Verify records still exist (soft delete, not hard delete)
        self.assertTrue(Customer.objects.filter(pk=self.customer1.pk).exists())
        self.assertTrue(Customer.objects.filter(pk=self.customer2.pk).exists())

    def test_bulk_delete_skips_unknown_uuids(self):
        self.client.force_login(self.admin)
        _add_perm(self.admin, Customer, 'delete_customer')
        url = reverse('commercial:cliente_bulk')
        fake_uuid = '00000000-0000-0000-0000-000000000000'
        data = {
            'action': 'delete',
            'uuids': [str(self.customer1.uuid), fake_uuid],
        }
        resp = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body['processed'], 1)
        self.assertEqual(body['skipped'], 1)

    def test_bulk_delete_skips_already_inactive(self):
        self.customer1.record_active = False
        self.customer1.save(update_fields=['record_active'])
        self.client.force_login(self.admin)
        _add_perm(self.admin, Customer, 'delete_customer')
        url = reverse('commercial:cliente_bulk')
        data = {
            'action': 'delete',
            'uuids': [str(self.customer1.uuid)],
        }
        resp = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body['processed'], 0)
        self.assertEqual(body['skipped'], 1)


class BulkPermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.user = _make_user('bulknoperm')
        cls.customer = natural_customer(
            _make_user('bulknopermcust'),
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )

    def test_unauthenticated_returns_redirect(self):
        url = reverse('commercial:cliente_bulk')
        data = {'action': 'export', 'uuids': [str(self.customer.uuid)]}
        resp = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 302)

    def test_no_permission_returns_403_for_delete(self):
        self.client.force_login(self.user)
        url = reverse('commercial:cliente_bulk')
        data = {'action': 'delete', 'uuids': [str(self.customer.uuid)]}
        resp = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 403)

    def test_no_permission_returns_403_for_export(self):
        self.client.force_login(self.user)
        url = reverse('commercial:cliente_bulk')
        data = {'action': 'export', 'uuids': [str(self.customer.uuid)]}
        resp = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 403)


class BulkInputSafetyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_superuser('bulksafeadmin')

    def test_unknown_action_returns_400(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:cliente_bulk')
        data = {'action': 'unknown', 'uuids': ['some-uuid']}
        resp = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_empty_uuids_returns_400(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:cliente_bulk')
        data = {'action': 'export', 'uuids': []}
        resp = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_missing_uuids_returns_400(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:cliente_bulk')
        data = {'action': 'export'}
        resp = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_invalid_json_returns_400(self):
        self.client.force_login(self.admin)
        url = reverse('commercial:cliente_bulk')
        resp = self.client.post(url, 'not-json', content_type='application/json')
        self.assertEqual(resp.status_code, 400)


class BulkUpdateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_superuser('bulkupdadmin')
        cls.customer = natural_customer(
            _make_user('bulkupdcust'),
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )
        cls.service = Service.objects.create(
            user=cls.admin,
            title='Bulk Update Service',
            summary='Test',
            service_type='commercial',
            code='BUP01',
            price=Decimal('50.00'),
        )
        cls.sub = ServiceSubscription.objects.create(
            customer=cls.customer,
            service=cls.service,
            payment_status='requested',
        )

    def test_bulk_update_payment_status(self):
        # Marcar `paid` exige el certificado entregado al cliente: sin ese
        # respaldo la suscripción quedaría cobrada sin comprobante. Por eso la
        # prueba del camino feliz crea el certificado antes de actualizar.
        Certificate.objects.create(
            subscription=self.sub,
            pdf=SimpleUploadedFile('bulk.pdf', b'%PDF-1.4 test', 'application/pdf'),
        )
        self.client.force_login(self.admin)
        _add_perm(self.admin, ServiceSubscription, 'change_subscription')
        url = reverse('commercial:suscripcion_bulk')
        data = {
            'action': 'update',
            'uuids': [str(self.sub.uuid)],
            'field': 'payment_status',
            'value': 'paid',
        }
        resp = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body['processed'], 1)
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.payment_status, 'paid')

    def test_bulk_update_rejects_non_allowlisted_field(self):
        self.client.force_login(self.admin)
        _add_perm(self.admin, ServiceSubscription, 'change_subscription')
        url = reverse('commercial:suscripcion_bulk')
        data = {
            'action': 'update',
            'uuids': [str(self.sub.uuid)],
            'field': 'customer',
            'value': '1',
        }
        resp = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_bulk_update_rejects_invalid_value(self):
        self.client.force_login(self.admin)
        _add_perm(self.admin, ServiceSubscription, 'change_subscription')
        url = reverse('commercial:suscripcion_bulk')
        data = {
            'action': 'update',
            'uuids': [str(self.sub.uuid)],
            'field': 'payment_status',
            'value': 'invalid_status',
        }
        resp = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 400)


class BulkAuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_superuser('bulkauditadmin')
        cls.customer = natural_customer(
            _make_user('bulkaudcust'),
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )

    def test_bulk_delete_creates_audit_entry(self):
        from django.contrib.admin.models import LogEntry

        self.client.force_login(self.admin)
        _add_perm(self.admin, Customer, 'delete_customer')
        url = reverse('commercial:cliente_bulk')
        initial_count = LogEntry.objects.count()
        data = {
            'action': 'delete',
            'uuids': [str(self.customer.uuid)],
        }
        self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertGreater(LogEntry.objects.count(), initial_count)
        entry = LogEntry.objects.latest('id')
        self.assertEqual(entry.user_id, self.admin.pk)
        self.assertIn('acción masiva', entry.change_message)
