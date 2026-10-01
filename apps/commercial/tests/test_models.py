from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.commercial.models import (
    Certificate,
    Contract,
    Customer,
    Invoice,
    InvoiceItem,
    Service,
    ServiceSubscription,
)
from apps.commercial.tests.test_views import disable_maintenance_mode
from apps.core.tests.base import FileHandlingTestCase


def _make_user(username='testuser', **kwargs):
    data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': f'{username}@example.com',
    }
    data.update(kwargs)
    return User.objects.create_user(username, **data)


class CustomerModelTests(TestCase):
    def test_create_natural_customer(self):
        user = _make_user('nat')
        customer = Customer.objects.create(
            client_type='natural',
            user=user,
            address='Calle 1 #123',
            phone='12345678',
            account='1234567890123456',
        )
        self.assertEqual(str(customer), user.get_full_name())
        self.assertIsNotNone(customer.uuid)
        self.assertTrue(customer.record_active)

    def test_create_juridica_customer(self):
        user = _make_user('jur')
        customer = Customer.objects.create(
            client_type='juridica',
            user=user,
            company_name='Empresa Test',
            reeup='123.4.5678',
            nit='12345678901',
            account='1234567890123456',
            address='Calle 2 #456',
            phone='87654321',
        )
        self.assertEqual(str(customer), 'Empresa Test')
        self.assertIsNotNone(customer.uuid)

    def test_custom_permissions(self):
        meta = Customer._meta
        perms = {p[0] for p in meta.permissions}
        expected = {
            'view_customer',
            'add_customer',
            'change_customer',
            'delete_customer',
        }
        self.assertEqual(perms, expected)
        self.assertEqual(meta.default_permissions, ())

    def test_soft_delete(self):
        user = _make_user('softdel')
        customer = Customer.objects.create(
            client_type='natural',
            user=user,
            address='Test',
            phone='12345678',
            account='1234567890123456',
        )
        customer.delete()
        customer.refresh_from_db()
        self.assertFalse(customer.record_active)
        self.assertIsNotNone(customer.deleted_at)

    def test_hard_delete(self):
        user = _make_user('harddel')
        customer = Customer.objects.create(
            client_type='natural',
            user=user,
            address='Test',
            phone='12345678',
            account='1234567890123456',
        )
        pk = customer.pk
        customer.hard_delete()
        self.assertFalse(Customer.objects.filter(pk=pk).exists())

    def test_unique_account(self):
        user1 = _make_user('u1')
        user2 = _make_user('u2')
        Customer.objects.create(
            client_type='natural',
            user=user1,
            address='Addr1',
            phone='11111111',
            account='1111111111111111',
        )
        with self.assertRaises(IntegrityError):
            Customer.objects.create(
                client_type='natural',
                user=user2,
                address='Addr2',
                phone='22222222',
                account='1111111111111111',
            )


class ServiceModelTests(FileHandlingTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('svcuser')

    def test_service_category_defaults_to_pronostico(self):
        service = Service.objects.create(
            user=self.user,
            title='Default Cat',
            summary='Sum',
            service_type='commercial',
        )
        self.assertEqual(service.service_category, 'pronostico')

    def test_period_days_alias_is_one(self):
        self.assertEqual(Service.PERIOD_DAYS, 1)

    def test_get_billing_period_display_pronostico(self):
        service = Service(
            user=self.user,
            title='P',
            summary='S',
            service_type='commercial',
            service_category='pronostico',
        )
        self.assertEqual(service.get_billing_period_display(), 'día')

    def test_get_billing_period_display_agrometeo(self):
        service = Service(
            user=self.user,
            title='A',
            summary='S',
            service_type='commercial',
            service_category='agrometeo',
        )
        self.assertEqual(service.get_billing_period_display(), 'mes')

    def test_get_price_per_period_display_pronostico(self):
        service = Service(
            user=self.user,
            title='P',
            summary='S',
            service_type='commercial',
            service_category='pronostico',
            price=Decimal('10.00'),
        )
        self.assertIn('10.00', service.get_price_per_period_display())
        self.assertIn('día', service.get_price_per_period_display())

    def test_get_price_per_period_display_agrometeo(self):
        service = Service(
            user=self.user,
            title='A',
            summary='S',
            service_type='commercial',
            service_category='agrometeo',
            price=Decimal('120.00'),
        )
        self.assertIn('120.00', service.get_price_per_period_display())
        self.assertIn('mes', service.get_price_per_period_display())

    def test_compute_end_date_agrometeo_no_overflow(self):
        from datetime import date as date_cls

        result = Service.compute_end_date(date_cls(2026, 1, 31), 2, 'agrometeo')
        self.assertEqual(result, date_cls(2026, 3, 31))

    def test_compute_end_date_pronostico_daily(self):
        from datetime import date as date_cls

        result = Service.compute_end_date(date_cls(2026, 1, 1), 5, 'pronostico')
        self.assertEqual(result, date_cls(2026, 1, 6))

    def test_compute_end_date_default_category_is_pronostico(self):
        from datetime import date as date_cls

        result = Service.compute_end_date(date_cls(2026, 2, 10), 3)
        self.assertEqual(result, date_cls(2026, 2, 13))

    def test_create_public_service(self):
        service = Service.objects.create(
            user=self.user,
            title='Test Service',
            summary='A summary',
            service_type='public',
        )
        self.assertEqual(str(service), 'Test Service')
        self.assertIsNotNone(service.uuid)

    def test_custom_permissions(self):
        meta = Service._meta
        perms = {p[0] for p in meta.permissions}
        expected = {
            'view_service',
            'add_service',
            'change_service',
            'delete_service',
        }
        self.assertEqual(perms, expected)
        self.assertEqual(meta.default_permissions, ())

    def test_get_image_url_without_image(self):
        service = Service.objects.create(
            user=self.user,
            title='No Image',
            summary='No image test',
            service_type='public',
        )
        self.assertTrue(service.get_image_url().endswith('dist/img/default.svg'))

    def test_get_image_url_with_image(self):
        image = SimpleUploadedFile(
            'test.png',
            b'PNG content',
            content_type='image/png',
        )
        service = Service.objects.create(
            user=self.user,
            title='With Image',
            summary='With image test',
            service_type='commercial',
            image=image,
            code='SV001',
            price=Decimal('100.00'),
        )
        self.assertIn('test.png', service.get_image_url())

    def test_soft_delete(self):
        service = Service.objects.create(
            user=self.user,
            title='To Delete',
            summary='Delete test',
            service_type='public',
        )
        service.delete()
        service.refresh_from_db()
        self.assertFalse(service.record_active)
        self.assertIsNotNone(service.deleted_at)

    def test_hard_delete(self):
        service = Service.objects.create(
            user=self.user,
            title='Hard Delete',
            summary='Hard del',
            service_type='public',
        )
        pk = service.pk
        service.hard_delete()
        self.assertFalse(Service.objects.filter(pk=pk).exists())

    def test_file_fields_defined(self):
        self.assertEqual(Service.file_fields, ['pdf', 'image'])


class ServiceSubscriptionModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('subuser')
        cls.customer = Customer.objects.create(
            client_type='natural',
            user=cls.user,
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )
        cls.service = Service.objects.create(
            user=cls.user,
            title='Comm Service',
            summary='Comm',
            service_type='commercial',
            code='C001',
            price=Decimal('50.00'),
        )

    def test_create_subscription(self):
        sub = ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.service,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )
        self.assertIsNotNone(sub.uuid)
        self.assertIn(self.service.title, str(sub))

    def test_quantity_defaults_to_one(self):
        sub = ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.service,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )
        self.assertEqual(sub.quantity, 1)

    def test_quantity_rejects_zero(self):
        sub = ServiceSubscription(
            customer=self.customer,
            service=self.service,
            quantity=0,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )
        with self.assertRaises(ValidationError):
            sub.full_clean()

    def test_get_quantity_period_display_pronostico(self):
        sub = ServiceSubscription(
            customer=self.customer,
            service=self.service,
            quantity=30,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )
        self.assertEqual(sub.get_quantity_period_display(), '30 días')

    def test_get_quantity_period_display_agrometeo(self):
        agrometeo = Service.objects.create(
            user=self.user,
            title='Agro',
            summary='A',
            service_type='commercial',
            service_category='agrometeo',
        )
        sub = ServiceSubscription(
            customer=self.customer,
            service=agrometeo,
            quantity=3,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=90),
        )
        self.assertEqual(sub.get_quantity_period_display(), '3 meses')

    def test_get_quantity_period_display_singular(self):
        sub = ServiceSubscription(
            customer=self.customer,
            service=self.service,
            quantity=1,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )
        self.assertEqual(sub.get_quantity_period_display(), '1 día')

    def test_custom_permissions(self):
        meta = ServiceSubscription._meta
        perms = {p[0] for p in meta.permissions}
        expected = {
            'view_subscription',
            'add_subscription',
            'change_subscription',
            'delete_subscription',
        }
        self.assertEqual(perms, expected)
        self.assertEqual(meta.default_permissions, ())

    def test_clean_rejects_invalid_dates(self):
        sub = ServiceSubscription(
            customer=self.customer,
            service=self.service,
            start_date=timezone.now(),
            end_date=timezone.now() - timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            sub.clean()

    def test_is_active_property(self):
        future = timezone.now() + timedelta(days=30)
        sub = ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.service,
            start_date=timezone.now(),
            end_date=future,
            payment_status='paid',
        )
        self.assertTrue(sub.is_active)
        self.assertEqual(sub.status_display, 'pagado')

    def test_is_active_expired(self):
        past = timezone.now() - timedelta(days=1)
        sub = ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.service,
            start_date=timezone.now() - timedelta(days=60),
            end_date=past,
            payment_status='paid',
        )
        self.assertFalse(sub.is_active)

    def test_status_display_values(self):
        sub = ServiceSubscription(
            customer=self.customer,
            service=self.service,
            payment_status='requested',
        )
        self.assertEqual(sub.status_display, 'solicitado')
        sub.payment_status = 'pending'
        self.assertEqual(sub.status_display, 'pendiente')
        sub.payment_status = 'paid'
        self.assertEqual(sub.status_display, 'pagado')

    def test_status_display_is_cancelled_by_soft_delete(self):
        """La baja lógica es lo que cancela, no un valor de `payment_status`.

        Anular ya marca `record_active=False`; llevar además un 'cancelled' en
        `payment_status` sería el mismo dato en dos campos, y la forma más
        segura de que se contradigan.
        """
        sub = ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.service,
            payment_status='paid',
        )
        self.assertEqual(sub.status_display, 'pagado')
        sub.delete()
        self.assertEqual(sub.status_display, 'cancelada')

    def test_status_display_ignores_the_elapsed_period(self):
        """Una suscripción pagada y vencida estuvo pagada.

        El periodo que terminó es un dato del servicio, no un estado de pago:
        mezclarlo hacía que un cobro correcto se leyera como 'expirado'.
        """
        sub = ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.service,
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=1),
            payment_status='paid',
        )
        self.assertFalse(sub.is_active)
        self.assertEqual(sub.status_display, 'pagado')

    def test_expired_is_not_a_valid_payment_status(self):
        from django.core.exceptions import ValidationError

        sub = ServiceSubscription(
            customer=self.customer,
            service=self.service,
            payment_status='expired',
        )
        with self.assertRaises(ValidationError):
            sub.full_clean()

    def test_soft_delete(self):
        sub = ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.service,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )
        sub.delete()
        sub.refresh_from_db()
        self.assertFalse(sub.record_active)
        self.assertIsNotNone(sub.deleted_at)


class InvoiceModelTests(FileHandlingTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('invuser')
        cls.customer = Customer.objects.create(
            client_type='natural',
            user=cls.user,
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )

    def test_create_invoice(self):
        invoice = Invoice.objects.create(
            customer=self.customer,
            number='INV-001',
            amount=Decimal('100.00'),
        )
        self.assertIn('INV-001', str(invoice))
        self.assertIsNotNone(invoice.uuid)
        self.assertFalse(invoice.is_cancelled)

    def test_custom_permissions(self):
        meta = Invoice._meta
        perms = {p[0] for p in meta.permissions}
        expected = {
            'view_invoice',
            'add_invoice',
            'change_invoice',
            'delete_invoice',
        }
        self.assertEqual(perms, expected)
        self.assertEqual(meta.default_permissions, ())

    def test_clean_rejects_zero_amount(self):
        invoice = Invoice(
            customer=self.customer,
            number='INV-002',
            amount=Decimal('0.00'),
        )
        with self.assertRaises(ValidationError):
            invoice.clean()

    def test_soft_delete(self):
        invoice = Invoice.objects.create(
            customer=self.customer,
            number='INV-003',
            amount=Decimal('50.00'),
        )
        invoice.delete()
        invoice.refresh_from_db()
        self.assertFalse(invoice.record_active)
        self.assertIsNotNone(invoice.deleted_at)

    def test_hard_delete(self):
        invoice = Invoice.objects.create(
            customer=self.customer,
            number='INV-004',
            amount=Decimal('75.00'),
        )
        pk = invoice.pk
        invoice.hard_delete()
        self.assertFalse(Invoice.objects.filter(pk=pk).exists())

    def test_file_fields_defined(self):
        self.assertEqual(Invoice.file_fields, ['pdf'])

    def test_unique_number(self):
        Invoice.objects.create(
            customer=self.customer,
            number='UNIQUE',
            amount=Decimal('10.00'),
        )
        with self.assertRaises(IntegrityError):
            Invoice.objects.create(
                customer=self.customer,
                number='UNIQUE',
                amount=Decimal('20.00'),
            )


class InvoiceItemModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('itemuser')
        cls.customer = Customer.objects.create(
            client_type='natural',
            user=cls.user,
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )
        cls.invoice = Invoice.objects.create(
            customer=cls.customer,
            number='INV-010',
            amount=Decimal('0.00'),
        )

    def test_create_item(self):
        item = InvoiceItem.objects.create(
            invoice=self.invoice,
            descripcion='Test item',
            cantidad=Decimal('2'),
            precio=Decimal('25.50'),
        )
        self.assertIsNotNone(item.uuid)
        self.assertEqual(item.importe, Decimal('51.00'))

    def test_custom_permissions(self):
        meta = InvoiceItem._meta
        perms = {p[0] for p in meta.permissions}
        expected = {
            'view_invoice_item',
            'add_invoice_item',
            'change_invoice_item',
            'delete_invoice_item',
        }
        self.assertEqual(perms, expected)
        self.assertEqual(meta.default_permissions, ())

    def test_save_computes_importe(self):
        item = InvoiceItem(
            invoice=self.invoice,
            descripcion='Compute test',
            cantidad=Decimal('3'),
            precio=Decimal('10.00'),
        )
        item.save()
        self.assertEqual(item.importe, Decimal('30.00'))

    def test_clean_rejects_zero_cantidad(self):
        item = InvoiceItem(
            invoice=self.invoice,
            descripcion='Bad qty',
            cantidad=Decimal('0'),
            precio=Decimal('10.00'),
        )
        with self.assertRaises(ValidationError):
            item.clean()

    def test_clean_rejects_zero_precio(self):
        item = InvoiceItem(
            invoice=self.invoice,
            descripcion='Bad price',
            cantidad=Decimal('1'),
            precio=Decimal('0'),
        )
        with self.assertRaises(ValidationError):
            item.clean()


class ContractModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('contuser')
        cls.customer = Customer.objects.create(
            client_type='natural',
            user=cls.user,
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )
        cls.service = Service.objects.create(
            user=cls.user,
            title='Svc',
            summary='Svc',
            service_type='commercial',
            code='C002',
            price=Decimal('30.00'),
        )
        cls.subscription = ServiceSubscription.objects.create(
            customer=cls.customer,
            service=cls.service,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )

    def test_create_contract(self):
        contract = Contract.objects.create(
            subscription=self.subscription,
            number='CONT-001',
            date=date.today(),
            commercial_registry='REG-001',
        )
        self.assertIn('CONT-001', str(contract))
        self.assertIsNotNone(contract.uuid)

    def test_custom_permissions(self):
        meta = Contract._meta
        perms = {p[0] for p in meta.permissions}
        expected = {
            'view_contract',
            'add_contract',
            'change_contract',
            'delete_contract',
        }
        self.assertEqual(perms, expected)
        self.assertEqual(meta.default_permissions, ())

    def test_soft_delete(self):
        contract = Contract.objects.create(
            subscription=self.subscription,
            number='CONT-002',
            date=date.today(),
            commercial_registry='REG-002',
        )
        contract.delete()
        contract.refresh_from_db()
        self.assertFalse(contract.record_active)
        self.assertIsNotNone(contract.deleted_at)


class CertificateModelTests(FileHandlingTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('certuser')
        cls.customer = Customer.objects.create(
            client_type='natural',
            user=cls.user,
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )
        cls.service = Service.objects.create(
            user=cls.user,
            title='Svc',
            summary='Svc',
            service_type='commercial',
            code='C003',
            price=Decimal('40.00'),
        )
        cls.subscription = ServiceSubscription.objects.create(
            customer=cls.customer,
            service=cls.service,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )

    def test_create_certificate(self):
        pdf = SimpleUploadedFile(
            'cert.pdf',
            b'PDF content',
            content_type='application/pdf',
        )
        cert = Certificate.objects.create(
            subscription=self.subscription,
            pdf=pdf,
        )
        self.assertIn(self.service.title, str(cert))
        self.assertIsNotNone(cert.uuid)
        self.assertIsNotNone(cert.issued_date)

    def test_custom_permissions(self):
        meta = Certificate._meta
        perms = {p[0] for p in meta.permissions}
        expected = {
            'view_certificate',
            'add_certificate',
            'change_certificate',
            'delete_certificate',
        }
        self.assertEqual(perms, expected)
        self.assertEqual(meta.default_permissions, ())

    def test_soft_delete(self):
        pdf = SimpleUploadedFile(
            'cert2.pdf',
            b'PDF content',
            content_type='application/pdf',
        )
        cert = Certificate.objects.create(
            subscription=self.subscription,
            pdf=pdf,
        )
        cert.delete()
        cert.refresh_from_db()
        self.assertFalse(cert.record_active)
        self.assertIsNotNone(cert.deleted_at)

    def test_file_fields_defined(self):
        self.assertEqual(Certificate.file_fields, ['pdf'])


class InvoiceDerivedStatusTests(TestCase):
    """La factura no tiene campo de estado: el pago se deriva de las líneas.

    El lote agrupa suscripciones y cada una se aprueba por separado, así que un
    campo propio en la factura sería una segunda fuente de verdad capaz de
    contradecir a la real.
    """

    def setUp(self):
        disable_maintenance_mode()
        customer = Customer.objects.create(
            client_type='natural',
            user=User.objects.create_user(username='invstatus', email='invstatus@example.com'),
            account='1',
            agency_bank='B',
            address='A',
            phone='9',
        )
        provider = User.objects.create_user(username='invprov', email='invprov@example.com')
        self.service = Service.objects.create(
            user=provider,
            title='S',
            summary='S',
            service_type='commercial',
            code='INV1',
            price=Decimal('10.00'),
        )
        self.customer = customer
        self.invoice = Invoice.objects.create(
            customer=customer, subscription=None, number='2026-7001', amount=20
        )

    def _sub(self, code, status):
        sub = ServiceSubscription.objects.create(
            customer=self.customer,
            service=Service.objects.create(
                user=self.service.user,
                title=f'S {code}',
                summary='S',
                service_type='commercial',
                code=code,
                price=Decimal('10.00'),
            ),
            payment_status=status,
        )
        InvoiceItem.objects.create(
            invoice=self.invoice,
            subscription=sub,
            codigo=code,
            descripcion=sub.service.title,
            cantidad=1,
            precio=Decimal('10.00'),
            importe=Decimal('10.00'),
        )
        return sub

    def test_invoice_without_subscriptions_is_pending(self):
        self.assertEqual(self.invoice.status_display, 'pendiente')

    def test_invoice_is_pending_while_any_subscription_is_unpaid(self):
        self._sub('S1', 'paid')
        self._sub('S2', 'pending')
        self.assertEqual(self.invoice.status_display, 'pendiente')

    def test_invoice_is_paid_when_every_subscription_is_paid(self):
        self._sub('S3', 'paid')
        self._sub('S4', 'paid')
        self.assertEqual(self.invoice.status_display, 'pagada')

    def test_cancelled_invoice_wins_over_paid_subscriptions(self):
        self._sub('S5', 'paid')
        self.invoice.is_cancelled = True
        self.invoice.save(update_fields=['is_cancelled'])
        self.assertEqual(self.invoice.status_display, 'cancelada')

    def test_annotation_matches_the_property_without_extra_queries(self):
        self._sub('S6', 'paid')
        self._sub('S7', 'paid')
        annotated = Invoice.objects.with_display_status().get(pk=self.invoice.pk)
        with self.assertNumQueries(0):
            self.assertEqual(annotated.status_display, 'pagada')
