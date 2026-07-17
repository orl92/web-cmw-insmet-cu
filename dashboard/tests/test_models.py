from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from dashboard.models import (
    Author,
    CompanySettings,
    Customer,
    EarlyWarning,
    EmailRecipient,
    EmailRecipientList,
    Forecasts,
    Invoice,
    InvoiceItem,
    Province,
    ScientificPublication,
    Service,
    ServiceSubscription,
    SiteConfiguration,
    Station,
    Town,
    WeatherReport,
    WeatherToday,
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
    def test_singleton_enforced(self):
        cs1 = CompanySettings.objects.create(
            pk=1, nombre='Test', direccion='Test',
            codigo_reeup='123.1.1234', nit='12345678901',
            cuenta_bancaria='1234567890123456', agencia_bancaria='Test',
            telefonos='12345678,87654321', registro_comercial='RC-001'
        )
        cs2 = CompanySettings(nombre='Other', direccion='Other',
                               codigo_reeup='999.9.9999', nit='99999999999',
                               cuenta_bancaria='9999999999999999', agencia_bancaria='Other',
                               telefonos='11111111', registro_comercial='RC-002')
        cs2.save()
        self.assertEqual(CompanySettings.objects.count(), 1)
        self.assertEqual(CompanySettings.objects.first().nombre, 'Other')

    def test_get_instance_creates_if_not_exists(self):
        obj = CompanySettings.get_instance()
        self.assertIsNotNone(obj)
        self.assertEqual(obj.pk, 1)


class ProvinceTests(TestCase):
    def test_create_province(self):
        p = Province.objects.create(name='Camagüey', code='CM')
        self.assertEqual(str(p), 'Camagüey')
        self.assertIsNotNone(p.uuid)

    def test_code_unique(self):
        Province.objects.create(name='Camagüey', code='CM')
        with self.assertRaises(Exception):
            Province.objects.create(name='Otro', code='CM')


class TownTests(TestCase):
    def test_create_town(self):
        prov = Province.objects.create(name='Camagüey', code='CM')
        town = Town.objects.create(name='Florida', province=prov, latitude=21.5, longitude=-78.2)
        self.assertEqual(str(town), 'Florida')
        self.assertEqual(town.province, prov)


class StationTests(TestCase):
    def test_create_station(self):
        prov = Province.objects.create(name='Camagüey', code='CM')
        station = Station.objects.create(name='Florida', number=123, province=prov, latitude=21.5, longitude=-78.2)
        self.assertEqual(str(station), 'Florida')
        self.assertEqual(station.number, 123)


class ForecastsTests(TestCase):
    def _make_forecast(self, forecast_date):
        return Forecasts.objects.create(
            date=forecast_date,
            lp='Luna Nueva', nlp='Cuarto Creciente', nlpd=forecast_date + timedelta(days=7),
            sunrise=time(6, 30), sunset=time(18, 30), uv_index=5,
        )

    def _add_region(self, forecast, region, period, temp, weather, wind_dir, wind_speed, sea_note=''):
        from dashboard.models import ForecastRegions
        return ForecastRegions.objects.create(
            forecast=forecast, region=region, period=period,
            temp=temp, weather=weather, wind_dir=wind_dir,
            wind_speed=wind_speed, sea_note=sea_note or None,
        )

    def _add_extended(self, forecast, day_num, fdate, min_temp, max_temp, weather):
        from dashboard.models import ForecastExtendedDay
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
        from dashboard.models import ForecastRegions
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
        from dashboard.models import ForecastExtendedDay
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
        from dashboard.models import ForecastExtendedDay
        f = Forecasts.objects.create(date=date.today(), lp='Luna Nueva',
                                      sunrise=time(6, 30), sunset=time(18, 30), uv_index=5,
                                      nlp='Cuarto Creciente', nlpd=date.today())
        with self.assertRaises(ValidationError):
            ForecastExtendedDay.objects.create(
                forecast=f, day_number=1, date=date.today(),
                min_temp=30, max_temp=20, weather='PN'
            )


class CustomerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('cust', 'cust@example.com', 'password',
                                             first_name='Test', last_name='User')

    def test_create_customer(self):
        customer = Customer.objects.create(
            company_name='Test Corp',
            reeup='123.1.1234',
            nit='12345678901',
            account='1234567890123456',
            agency_bank='Test Bank',
            address='Test Address',
            user=self.user,
            phone='12345678',
            accept_terms=True,
        )
        self.assertEqual(str(customer), 'Test Corp')
        self.assertIsNotNone(customer.uuid)

    def test_invalid_reeup_raises_error(self):
        customer = Customer(
            company_name='Test Corp',
            reeup='invalid',
            nit='12345678901',
            account='1234567890123456',
            address='Test',
            user=self.user,
            phone='12345678',
        )
        with self.assertRaises(ValidationError):
            customer.full_clean()


class ServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('svc', 'svc@example.com', 'password',
                                             first_name='Test', last_name='User')

    def test_create_service(self):
        service = Service.objects.create(
            title='Test Service',
            summary='Summary',
            user=self.user,
            service_type='public',
        )
        self.assertEqual(str(service), 'Test Service')
        self.assertIsNotNone(service.uuid)

    def test_get_image_url_returns_default_when_no_image(self):
        service = Service.objects.create(title='Svc', summary='S', user=self.user)
        url = service.get_image_url()
        self.assertIn('default.svg', url)


class ServiceSubscriptionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('sub', 'sub@example.com', 'password',
                                             first_name='Test', last_name='User')
        cls.customer = Customer.objects.create(
            company_name='Sub Corp', reeup='111.1.1111', nit='11111111111',
            account='1111111111111111', address='Addr', user=cls.user, phone='11111111')
        cls.service = Service.objects.create(title='Sub Svc', summary='S', user=cls.user)

    def test_soft_delete_sets_record_active_false(self):
        sub = ServiceSubscription.objects.create(customer=self.customer, service=self.service)
        sub.delete()
        self.assertFalse(sub.record_active)
        self.assertIsNotNone(sub.deleted_at)
        self.assertTrue(ServiceSubscription.objects.filter(pk=sub.pk).exists())

    def test_hard_delete_removes_record(self):
        sub = ServiceSubscription.objects.create(customer=self.customer, service=self.service)
        pk = sub.pk
        sub.hard_delete()
        self.assertFalse(ServiceSubscription.objects.filter(pk=pk).exists())

    def test_is_active_property(self):
        future = timezone.now() + timedelta(days=30)
        sub = ServiceSubscription.objects.create(
            customer=self.customer, service=self.service,
            payment_status='paid', end_date=future)
        self.assertTrue(sub.is_active)

    def test_is_active_false_when_expired(self):
        past = timezone.now() - timedelta(days=1)
        sub = ServiceSubscription.objects.create(
            customer=self.customer, service=self.service,
            payment_status='paid', end_date=past)
        self.assertFalse(sub.is_active)

    def test_start_date_before_end_date(self):
        sub = ServiceSubscription(
            customer=self.customer, service=self.service,
            start_date=timezone.now() + timedelta(days=5),
            end_date=timezone.now(),
        )
        with self.assertRaises(ValidationError):
            sub.full_clean()


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


class ScientificPublicationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = Author.objects.create(first_name='John', last_name='Doe')

    def test_create_publication(self):
        pdf = SimpleUploadedFile('pub.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        pub = ScientificPublication.objects.create(
            title='Test Paper', author=self.author,
            publication_date=date.today(), summary='Abstract', pdf_file=pdf)
        self.assertEqual(str(pub), 'Test Paper')

    def test_create_author(self):
        author = Author.objects.create(first_name='Jane', last_name='Smith')
        self.assertEqual(str(author), 'Jane Smith')


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
            summary=f'Test {report_type}', type=report_type,
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
