from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.crm.models import Customer, Service, ServiceSubscription
from apps.dashboard.models import (
    Certificate,
    CompanySettings,
    Contract,
    EarlyWarning,
    EmailRecipient,
    EmailRecipientList,
    Forecasts,
    Invoice,
    InvoiceItem,
    SiteConfiguration,
    StormWarning,
    TropicalCyclone,
    WeatherReport,
)

from django.core.files.uploadedfile import SimpleUploadedFile


class SiteConfigurationTests(TestCase):
    def test_maintenance_mode_defaults_to_true(self):
        config = SiteConfiguration.objects.create()
        self.assertTrue(config.maintenance_mode)

    def test_str_returns_description(self):
        config = SiteConfiguration.objects.create()
        self.assertIn('Modo Mantenimiento', str(config))


class CompanySettingsTests(TestCase):
    def test_get_instance_returns_object(self):
        obj = CompanySettings.get_instance()
        self.assertIsNotNone(obj)
        self.assertIsNotNone(obj.uuid)

    def test_get_instance_reuses_existing(self):
        obj1 = CompanySettings.get_instance()
        obj2 = CompanySettings.get_instance()
        self.assertEqual(obj1.pk, obj2.pk)


class ForecastsTests(TestCase):
    def _make_forecast(self, forecast_date):
        return Forecasts.objects.create(
            date=forecast_date,
            lp='Luna Nueva', nlp='Cuarto Creciente', nlpd=forecast_date + timedelta(days=7),
            sunrise=time(6, 30), sunset=time(18, 30), uv_index=5,
        )

    def _add_region(self, forecast, region, period, temp, weather, wind_dir, wind_speed, sea_note=''):
        from apps.dashboard.models import ForecastRegions
        return ForecastRegions.objects.create(
            forecast=forecast, region=region, period=period,
            temp=temp, weather=weather, wind_dir=wind_dir,
            wind_speed=wind_speed, sea_note=sea_note or None,
        )

    def _add_extended(self, forecast, day_num, fdate, min_temp, max_temp, weather):
        from apps.dashboard.models import ForecastExtendedDay
        return ForecastExtendedDay.objects.create(
            forecast=forecast, day_number=day_num,
            date=fdate, min_temp=min_temp, max_temp=max_temp, weather=weather,
        )

    def test_create_forecast(self):
        forecast = self._make_forecast(date.today())
        self.assertIn('Pronóstico detallado', str(forecast))

    def test_date_unique(self):
        self._make_forecast(date.today())
        with self.assertRaises(Exception):
            self._make_forecast(date.today())

    def test_region_properties_return_dicts(self):
        forecast = self._make_forecast(date.today())
        self._add_region(forecast, 'north', 'morning', 25, 'PN', 'N', '10', 'TQ')
        self._add_region(forecast, 'north', 'afternoon', 30, 'N', 'NE', '15', 'PO')
        self._add_region(forecast, 'north', 'night', 22, 'PARCN', 'E', '5', 'TQ')
        self._add_region(forecast, 'interior', 'morning', 24, 'PN', 'N', '10', None)
        self._add_region(forecast, 'interior', 'afternoon', 29, 'N', 'NE', '15', None)
        self._add_region(forecast, 'interior', 'night', 21, 'PARCN', 'E', '5', None)
        self._add_region(forecast, 'south', 'morning', 23, 'PN', 'N', '10', 'TQ')
        self._add_region(forecast, 'south', 'afternoon', 28, 'N', 'NE', '15', 'PO')
        self._add_region(forecast, 'south', 'night', 20, 'PARCN', 'E', '5', 'TQ')
        self.assertIn('morning', forecast.north)
        self.assertIn('afternoon', forecast.interior)
        self.assertIn('night', forecast.south)
        self.assertEqual(forecast.north['morning']['temp'], 25)
        self.assertEqual(forecast.regions.count(), 9)

    def test_extended_days_property_returns_5_days(self):
        forecast = self._make_forecast(date.today())
        for i in range(1, 6):
            self._add_extended(forecast, i, date.today() + timedelta(days=i), 20, 30, 'PN')
        days = forecast.extended_forecast
        self.assertEqual(len(days), 5)
        self.assertEqual(days[0].day_number, 1)
        self.assertEqual(forecast.extended_days.count(), 5)


class ForecastRegionsTests(TestCase):
    def test_create_region_row(self):
        from apps.dashboard.models import ForecastRegions
        f = Forecasts.objects.create(date=date.today(), lp='Luna Nueva',
                                      sunrise=time(6, 30), sunset=time(18, 30), uv_index=5,
                                      nlp='Cuarto Creciente', nlpd=date.today())
        region = ForecastRegions.objects.create(
            forecast=f, region='north', period='morning',
            temp=25, weather='PN', wind_dir='N', wind_speed='10', sea_note='TQ'
        )
        self.assertIn('Costa Norte', str(region))
        self.assertEqual(region.temp, 25)
        self.assertIsNotNone(region.weather_icon)


class ForecastExtendedDayTests(TestCase):
    def test_create_extended_day(self):
        from apps.dashboard.models import ForecastExtendedDay
        f = Forecasts.objects.create(date=date.today(), lp='Luna Nueva',
                                      sunrise=time(6, 30), sunset=time(18, 30), uv_index=5,
                                      nlp='Cuarto Creciente', nlpd=date.today())
        day = ForecastExtendedDay.objects.create(
            forecast=f, day_number=1, date=date.today(),
            min_temp=20, max_temp=30, weather='PN'
        )
        self.assertEqual(day.day_number, 1)
        self.assertIsNotNone(day.weather_icon)

    def test_min_temp_less_than_max_temp(self):
        from apps.dashboard.models import ForecastExtendedDay
        f = Forecasts.objects.create(date=date.today(), lp='Luna Nueva',
                                      sunrise=time(6, 30), sunset=time(18, 30), uv_index=5,
                                      nlp='Cuarto Creciente', nlpd=date.today())
        with self.assertRaises(ValidationError):
            ForecastExtendedDay.objects.create(
                forecast=f, day_number=1, date=date.today(),
                min_temp=30, max_temp=20, weather='PN'
            )


class InvoiceAndItemTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('inv', 'inv@example.com', 'password',
                                             first_name='Test', last_name='User')
        cls.customer = Customer.objects.create(
            company_name='Inv Corp', reeup='222.2.2222', nit='22222222222',
            account='2222222222222222', address='Addr', user=cls.user, phone='22222222')
        cls.service = Service.objects.create(title='Inv Svc', summary='S', user=cls.user)
        cls.subscription = ServiceSubscription.objects.create(customer=cls.customer, service=cls.service)

    def test_invoice_creation(self):
        invoice = Invoice.objects.create(
            subscription=self.subscription, customer=self.customer,
            number='INV-001', amount=100.00)
        self.assertIn('INV-001', str(invoice))
        self.assertFalse(invoice.is_cancelled)

    def test_invoice_item_auto_calculates_importe(self):
        invoice = Invoice.objects.create(
            subscription=self.subscription, customer=self.customer,
            number='INV-002', amount=100.00)
        item = InvoiceItem.objects.create(
            invoice=invoice, subscription=self.subscription,
            descripcion='Test item', cantidad=5, precio=10.00)
        self.assertEqual(item.importe, 50.00)

    def test_invoice_amount_must_be_positive(self):
        invoice = Invoice(
            subscription=self.subscription, customer=self.customer,
            number='INV-BAD', amount=0)
        with self.assertRaises(ValidationError):
            invoice.full_clean()

    def test_invoice_item_cantidad_must_be_positive(self):
        invoice = Invoice.objects.create(
            subscription=self.subscription, customer=self.customer,
            number='INV-003', amount=100.00)
        with self.assertRaises(ValidationError):
            InvoiceItem.objects.create(
                invoice=invoice, descripcion='Bad item',
                cantidad=0, precio=10.00)

    def test_invoice_item_precio_must_be_positive(self):
        invoice = Invoice.objects.create(
            subscription=self.subscription, customer=self.customer,
            number='INV-004', amount=100.00)
        with self.assertRaises(ValidationError):
            InvoiceItem.objects.create(
                invoice=invoice, descripcion='Bad item',
                cantidad=5, precio=0)


class EarlyWarningTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('warn', 'warn@example.com', 'password',
                                             first_name='Test', last_name='User')

    def test_create_early_warning(self):
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        warning = EarlyWarning.objects.create(
            user=self.user, summary='Test warning', file=pdf,
            valid_until=timezone.now() + timedelta(days=1))
        self.assertIn('Test warning', str(warning))


class EmailRecipientListTests(TestCase):
    def test_create_list_with_recipients(self):
        lst = EmailRecipientList.objects.create(name='Test List', description='Desc')
        recipient = EmailRecipient.objects.create(email='test@example.com', recipient_list=lst)
        self.assertEqual(str(lst), 'Test List')
        self.assertEqual(str(recipient), 'test@example.com')
        self.assertEqual(lst.recipients.count(), 1)


class WeatherReportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('wreport', 'w@example.com', 'password',
                                             first_name='Test', last_name='User')

    def _make_report(self, report_type='today'):
        return WeatherReport.objects.create(
            user=self.user, date=timezone.now(),
            summary=f'Test {report_type}', report_type=report_type,
        )

    def test_create_report_today(self):
        r = self._make_report('today')
        self.assertIn('Hoy', str(r))

    def test_create_report_tomorrow(self):
        r = self._make_report('tomorrow')
        self.assertIn('Mañana', str(r))

    def test_create_report_commentary(self):
        r = self._make_report('commentary')
        self.assertIn('Comentario', str(r))

    def test_create_report_note(self):
        r = self._make_report('note')
        self.assertIn('Nota', str(r))

    def test_report_summary(self):
        r = self._make_report('today')
        self.assertEqual(r.summary, 'Test today')

    def test_report_str(self):
        r = self._make_report('today')
        self.assertIn('Hoy', str(r))
        self.assertIn(str(r.date), str(r))


class TropicalCycloneTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('tc', 'tc@example.com', 'password')

    def test_create_tropical_cyclone(self):
        pdf = SimpleUploadedFile('tc.pdf', b'%PDF-1.4 tc', content_type='application/pdf')
        tc = TropicalCyclone.objects.create(
            user=self.user, summary='Test cyclone', file=pdf,
            valid_until=timezone.now() + timedelta(days=1))
        self.assertIn('Test cyclone', str(tc))
        self.assertIsNotNone(tc.uuid)

    def test_file_field_upload(self):
        pdf = SimpleUploadedFile('tc2.pdf', b'%PDF-1.4 tc2', content_type='application/pdf')
        tc = TropicalCyclone.objects.create(
            user=self.user, summary='Cyclone with file', file=pdf,
            valid_until=timezone.now() + timedelta(days=1))
        self.assertTrue(tc.file.name.endswith('.pdf'))
        self.assertTrue(tc.file.name.startswith('pdf/'))


class StormWarningTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('storm', 'storm@example.com', 'password')

    def test_create_storm_warning(self):
        pdf = SimpleUploadedFile('storm.pdf', b'%PDF-1.4 storm', content_type='application/pdf')
        sw = StormWarning.objects.create(
            user=self.user, summary='Test storm', file=pdf,
            valid_until=timezone.now() + timedelta(days=1))
        self.assertIn('Test storm', str(sw))
        self.assertIsNotNone(sw.uuid)

    def test_file_field_upload(self):
        pdf = SimpleUploadedFile('storm2.pdf', b'%PDF-1.4 storm2', content_type='application/pdf')
        sw = StormWarning.objects.create(
            user=self.user, summary='Storm with file', file=pdf,
            valid_until=timezone.now() + timedelta(days=1))
        self.assertTrue(sw.file.name.endswith('.pdf'))
        self.assertTrue(sw.file.name.startswith('pdf/'))


class ContractTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('contract', 'contract@example.com', 'password')
        cls.customer = Customer.objects.create(
            company_name='Contract Corp', reeup='333.1.3333', nit='33333333333',
            account='3333333333333333', address='Addr', user=cls.user, phone='33333333')
        cls.service = Service.objects.create(title='Contract Svc', summary='S', user=cls.user)
        cls.subscription = ServiceSubscription.objects.create(
            customer=cls.customer, service=cls.service)

    def test_create_contract(self):
        contract = Contract.objects.create(
            subscription=self.subscription, number='CTR-001',
            date=timezone.now().date(), commercial_registry='REG-001')
        self.assertIn('CTR-001', str(contract))
        self.assertIsNotNone(contract.uuid)

    def test_soft_delete_sets_record_active_false(self):
        contract = Contract.objects.create(
            subscription=self.subscription, number='CTR-002',
            date=timezone.now().date(), commercial_registry='REG-002')
        contract.delete()
        self.assertFalse(contract.record_active)
        self.assertIsNotNone(contract.deleted_at)
        self.assertTrue(Contract.objects.filter(pk=contract.pk).exists())

    def test_hard_delete_removes_record(self):
        contract = Contract.objects.create(
            subscription=self.subscription, number='CTR-003',
            date=timezone.now().date(), commercial_registry='REG-003')
        pk = contract.pk
        contract.hard_delete()
        self.assertFalse(Contract.objects.filter(pk=pk).exists())


class CertificateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('cert', 'cert@example.com', 'password')
        cls.customer = Customer.objects.create(
            company_name='Cert Corp', reeup='444.1.4444', nit='44444444444',
            account='4444444444444444', address='Addr', user=cls.user, phone='44444444')
        cls.service = Service.objects.create(title='Cert Svc', summary='S', user=cls.user)
        cls.subscription = ServiceSubscription.objects.create(
            customer=cls.customer, service=cls.service)

    def test_create_certificate(self):
        pdf = SimpleUploadedFile('cert.pdf', b'%PDF-1.4 cert', content_type='application/pdf')
        cert = Certificate.objects.create(
            subscription=self.subscription, pdf=pdf)
        self.assertIn('Cert Svc', str(cert))
        self.assertIn('Cert Corp', str(cert))
        self.assertIsNotNone(cert.uuid)

    def test_soft_delete_sets_record_active_false(self):
        pdf = SimpleUploadedFile('cert_soft.pdf', b'%PDF-1.4 soft', content_type='application/pdf')
        cert = Certificate.objects.create(
            subscription=self.subscription, pdf=pdf)
        cert.delete()
        self.assertFalse(cert.record_active)
        self.assertIsNotNone(cert.deleted_at)
        self.assertTrue(Certificate.objects.filter(pk=cert.pk).exists())

    def test_hard_delete_removes_record(self):
        pdf = SimpleUploadedFile('cert_hard.pdf', b'%PDF-1.4 hard', content_type='application/pdf')
        cert = Certificate.objects.create(
            subscription=self.subscription, pdf=pdf)
        pk = cert.pk
        cert.hard_delete()
        self.assertFalse(Certificate.objects.filter(pk=pk).exists())

    def test_hard_delete_cleans_up_file(self):
        import os
        pdf = SimpleUploadedFile('cert_cleanup.pdf', b'%PDF-1.4 cleanup', content_type='application/pdf')
        cert = Certificate.objects.create(
            subscription=self.subscription, pdf=pdf)
        file_path = cert.pdf.path
        self.assertTrue(os.path.exists(file_path))
        cert.hard_delete()
        self.assertFalse(os.path.exists(file_path))

    def test_file_fields_defined(self):
        self.assertEqual(Certificate.file_fields, ['pdf'])
