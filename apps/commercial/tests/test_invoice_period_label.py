from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from apps.commercial.models import Invoice
from apps.commercial.tests.factories import natural_customer


def _make_customer(username='labelcust'):
    customer = natural_customer(
        User.objects.create_user(username, f'{username}@ex.com', 'pass'),
        account='1234567890123456',
        agency_bank='BANDEC',
        address='Calle 10',
        phone='12345678',
    )
    return customer


class InvoicePeriodLabelTests(TestCase):
    def test_un_mes(self):
        invoice = Invoice.objects.create(
            customer=_make_customer('t1'),
            number='INV-001',
            amount=Decimal('100.00'),
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
        )
        self.assertEqual(invoice.period_label, 'Mes de enero de 2026')

    def test_dos_meses_mismo_ano(self):
        invoice = Invoice.objects.create(
            customer=_make_customer('t2'),
            number='INV-002',
            amount=Decimal('100.00'),
            period_start=date(2026, 1, 1),
            period_end=date(2026, 2, 28),
        )
        self.assertEqual(invoice.period_label, 'De enero a febrero de 2026')

    def test_cruza_ano(self):
        invoice = Invoice.objects.create(
            customer=_make_customer('t3'),
            number='INV-003',
            amount=Decimal('100.00'),
            period_start=date(2025, 12, 1),
            period_end=date(2026, 1, 31),
        )
        self.assertEqual(invoice.period_label, 'De diciembre de 2025 a enero de 2026')
