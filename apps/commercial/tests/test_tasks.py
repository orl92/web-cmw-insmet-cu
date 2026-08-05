from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from apps.commercial.models import (
    Customer,
    Invoice,
    InvoiceItem,
    Service,
    ServiceSubscription,
)


class InvoiceUtilsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            'invutil',
            'i@i.com',
            'pass',
            first_name='Test',
            last_name='User',
        )
        cls.customer = Customer.objects.create(
            client_type='natural',
            user=cls.user,
            address='Addr',
            phone='12345678',
            account='1234567890123456',
        )
        cls.invoice = Invoice.objects.create(
            customer=cls.customer,
            number='INV-UTIL',
            amount=Decimal('100.00'),
        )
        InvoiceItem.objects.create(
            invoice=cls.invoice,
            descripcion='Item 1',
            cantidad=1,
            precio=Decimal('100.00'),
        )

    @patch('apps.commercial.views.invoice_utils.render_to_string')
    @patch('apps.commercial.views.invoice_utils.EmailMessage')
    def test_enviar_correo_factura(self, mock_email_cls, mock_render):
        mock_render.return_value = '<html></html>'
        mock_email = MagicMock()
        mock_email_cls.return_value = mock_email
        from apps.commercial.views.invoice_utils import enviar_correo_factura

        result = enviar_correo_factura(
            self.invoice,
            self.customer,
            base_url='http://testserver/',
        )
        self.assertTrue(result)
        self.invoice.refresh_from_db()
        self.assertTrue(self.invoice.email_sent)

    @patch('apps.commercial.views.invoice_utils.render_to_string')
    @patch('apps.commercial.views.invoice_utils.EmailMessage')
    def test_enviar_correo_factura_failure_logs_error(self, mock_email_cls, mock_render):
        mock_render.return_value = '<html></html>'
        mock_email = MagicMock()
        mock_email.send.side_effect = Exception('SMTP error')
        mock_email_cls.return_value = mock_email
        from apps.commercial.views.invoice_utils import enviar_correo_factura

        result = enviar_correo_factura(
            self.invoice,
            self.customer,
            base_url='http://testserver/',
        )
        self.assertFalse(result)
        self.invoice.refresh_from_db()
        self.assertIn('SMTP error', self.invoice.email_error or '')


class CertificateEmailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            'certmail',
            'c@c.com',
            'pass',
            first_name='Test',
            last_name='User',
        )
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
            code='C200',
            price=Decimal('80.00'),
        )
        cls.sub = ServiceSubscription.objects.create(
            customer=cls.customer,
            service=cls.service,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            payment_status='paid',
        )

    def test_enviar_correo_certificado_sin_certificado(self):
        from apps.commercial.views.subscriptions import (
            enviar_correo_certificado,
        )

        sub_no_cert = ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.service,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )
        result = enviar_correo_certificado(sub_no_cert)
        self.assertFalse(result)

    def test_enviar_correo_certificado_sin_email_usuario(self):
        from apps.commercial.views.subscriptions import (
            enviar_correo_certificado,
        )

        user_no_email = User.objects.create_user(
            'noemail',
            '',
            'pass',
            first_name='No',
            last_name='Email',
        )
        customer_no_email = Customer.objects.create(
            client_type='natural',
            user=user_no_email,
            address='Addr',
            phone='12345678',
            account='9999999999999999',
        )
        sub = ServiceSubscription.objects.create(
            customer=customer_no_email,
            service=self.service,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )
        result = enviar_correo_certificado(sub)
        self.assertFalse(result)
