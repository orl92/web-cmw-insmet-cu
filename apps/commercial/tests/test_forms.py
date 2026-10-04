import struct
import zlib
from datetime import date, datetime, timedelta
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
from apps.commercial.forms.invoice import InvoiceForm, InvoiceItemForm
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
from apps.commercial.tests.factories import natural_customer


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
            'first_name': 'Ana',
            'last_name': 'Norte',
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
        # La persona natural sí necesita documento de identidad: es el único dato
        # con el que se la identifica en la factura.
        data['identity_document'] = '34111234567'
        form = CustomerForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_natural_requires_identity_document(self):
        data = self._valid_juridica_data()
        data['client_type'] = 'natural'
        data['company_name'] = ''
        data['reeup'] = ''
        data['nit'] = ''
        data['identity_document'] = ''
        form = CustomerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('identity_document', form.errors)

    def test_juridica_does_not_require_identity_document(self):
        data = self._valid_juridica_data()
        data['identity_document'] = ''
        form = CustomerForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_natural_identity_document_se_guarda(self):
        data = self._valid_juridica_data()
        data['client_type'] = 'natural'
        data['company_name'] = ''
        data['reeup'] = ''
        data['nit'] = ''
        data['identity_document'] = '  34111234567  '
        form = CustomerForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        customer = form.save()
        # Se guarda sin los espacios: el `strip` del cleaner, igual que con el resto.
        self.assertEqual(customer.identity_document, '34111234567')

    def test_unique_identity_document(self):
        u1 = _make_user('u1')
        natural_customer(
            u1,
            identity_document='34111234567',
            account='1111111111111111',
            address='Addr',
            phone='11111111',
        )
        data = self._valid_juridica_data()
        data['client_type'] = 'natural'
        data['company_name'] = ''
        data['reeup'] = ''
        data['nit'] = ''
        data['identity_document'] = '34111234567'
        data['username'] = 'newuser2'
        data['email'] = 'u2@example.com'
        data['account'] = '2222222222222222'
        form = CustomerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('identity_document', form.errors)

    def test_identity_document_vacio_no_choca_con_unico(self):
        """Dos jurídicas sin documento no se pisan entre sí: la unicidad solo se
        compara cuando el campo tiene valor, porque es opcional para ellas."""
        Customer.objects.create(
            client_type='juridica',
            user=_make_user('u1'),
            company_name='Existing',
            identity_document=None,
            reeup='111.1.1111',
            nit='11111111111',
            account='1111111111111111',
            address='Addr',
            phone='11111111',
        )
        data = self._valid_juridica_data()
        data['identity_document'] = ''
        data['username'] = 'newuser2'
        data['email'] = 'u2@example.com'
        data['account'] = '2222222222222222'
        form = CustomerForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.save().identity_document)

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

    def test_nombre_y_apellido_son_obligatorios(self):
        # Sin ellos el User nace sin nombre: `display_name` del cliente natural
        # cae al username y `CheckUserProfileMiddleware` manda a actualizar el
        # perfil en cada request.
        data = self._valid_juridica_data()
        data['first_name'] = ''
        data['last_name'] = ''
        form = CustomerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)

    def test_nombre_y_apellido_se_guardan_en_el_usuario(self):
        form = CustomerForm(data=self._valid_juridica_data())
        self.assertTrue(form.is_valid(), form.errors)
        customer = form.save()
        self.assertEqual(customer.user.first_name, 'Ana')
        self.assertEqual(customer.user.last_name, 'Norte')

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

    def _juridica_data(self, **kwargs):
        data = {
            'client_type': 'juridica',
            'company_name': 'New Name',
            'reeup': '111.1.1111',
            'nit': '11111111111',
            'account': '1111111111111111',
            'agency_bank': 'New Bank',
            'address': 'New address',
            'phone': '11111111',
            'email': 'updated@example.com',
        }
        data.update(kwargs)
        return data

    def test_juridica_no_requiere_identity_document(self):
        form = CustomerUpdateForm(instance=self.customer, data=self._juridica_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_natural_requiere_identity_document(self):
        form = CustomerUpdateForm(
            instance=self.customer,
            data=self._juridica_data(
                client_type='natural', company_name='', reeup='', nit='', identity_document=''
            ),
        )
        self.assertFalse(form.is_valid())
        self.assertIn('identity_document', form.errors)

    def test_natural_guarda_identity_document(self):
        form = CustomerUpdateForm(
            instance=self.customer,
            data=self._juridica_data(
                client_type='natural',
                company_name='',
                reeup='',
                nit='',
                identity_document='34111234567',
            ),
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().identity_document, '34111234567')

    def test_update_acepta_su_propio_identity_document(self):
        """La unicidad excluye la instancia: reenviar el valor sin tocar no es
        un choque con uno mismo (mismo criterio que reeup/nit)."""
        self.customer.identity_document = '34111234567'
        self.customer.save(update_fields=['identity_document'])

        form = CustomerUpdateForm(
            instance=self.customer,
            data=self._juridica_data(
                client_type='natural',
                company_name='',
                reeup='',
                nit='',
                identity_document='34111234567',
            ),
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_update_rechaza_el_documento_de_otro(self):
        otro = User.objects.create_user('otrocliente', 'otro@example.com', 'pass')
        natural_customer(
            otro,
            identity_document='34999999999',
            account='3333333333333333',
            address='Addr',
            phone='11111111',
        )

        form = CustomerUpdateForm(
            instance=self.customer,
            data=self._juridica_data(
                client_type='natural',
                company_name='',
                reeup='',
                nit='',
                identity_document='34999999999',
            ),
        )
        self.assertFalse(form.is_valid())
        self.assertIn('identity_document', form.errors)


class CustomerForUserFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('foruser')

    def test_valid_form(self):
        form = CustomerForUserForm(
            user=self.user,
            data={
                'first_name': 'Ana',
                'last_name': 'Norte',
                'client_type': 'natural',
                'identity_document': '34111234567',
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

    def test_natural_requiere_identity_document(self):
        form = CustomerForUserForm(
            user=self.user,
            data={
                'first_name': 'Ana',
                'last_name': 'Norte',
                'client_type': 'natural',
                'account': '1234567890123456',
                'agency_bank': 'Banco Test',
                'address': 'Addr',
                'phone': '12345678',
                'email': 'foruser@example.com',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn('identity_document', form.errors)

    def test_juridica_no_requiere_identity_document(self):
        form = CustomerForUserForm(
            user=self.user,
            data={
                'first_name': 'Ana',
                'last_name': 'Norte',
                'client_type': 'juridica',
                'company_name': 'Empresa S.A.',
                'reeup': '123.4.5678',
                'nit': '12345678901',
                'account': '1234567890123456',
                'agency_bank': 'Banco Test',
                'address': 'Addr',
                'phone': '12345678',
                'email': 'foruser@example.com',
            },
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_nombre_y_apellido_son_obligatorios(self):
        form = CustomerForUserForm(
            user=self.user,
            data={
                'client_type': 'juridica',
                'company_name': 'Empresa S.A.',
                'reeup': '123.4.5678',
                'nit': '12345678901',
                'account': '1234567890123456',
                'agency_bank': 'Banco Test',
                'address': 'Addr',
                'phone': '12345678',
                'email': 'foruser@example.com',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)

    def test_prellena_el_nombre_del_usuario_existente(self):
        form = CustomerForUserForm(user=self.user)
        self.assertEqual(form.fields['first_name'].initial, self.user.first_name)
        self.assertEqual(form.fields['last_name'].initial, self.user.last_name)

    def test_guarda_el_nombre_sobre_el_usuario_existente(self):
        form = CustomerForUserForm(
            user=self.user,
            data={
                'first_name': 'Ana',
                'last_name': 'Sur',
                'client_type': 'juridica',
                'company_name': 'Empresa S.A.',
                'reeup': '123.4.5678',
                'nit': '12345678901',
                'account': '1234567890123456',
                'agency_bank': 'Banco Test',
                'address': 'Addr',
                'phone': '12345678',
                'email': 'foruser@example.com',
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        customer = form.save()
        self.user.refresh_from_db()
        self.assertEqual(customer.user.first_name, 'Ana')
        self.assertEqual(customer.user.last_name, 'Sur')

    def test_rechaza_identity_document_duplicado(self):
        otro = User.objects.create_user('foruser2', 'foruser2@example.com', 'pass')
        natural_customer(
            otro,
            identity_document='34111234567',
            account='9999999999999999',
            address='Addr',
            phone='11111111',
        )

        form = CustomerForUserForm(
            user=self.user,
            data={
                'first_name': 'Ana',
                'last_name': 'Norte',
                'client_type': 'natural',
                'identity_document': '34111234567',
                'account': '1234567890123456',
                'agency_bank': 'Banco Test',
                'address': 'Addr',
                'phone': '12345678',
                'email': 'foruser@example.com',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn('identity_document', form.errors)


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
        image = SimpleUploadedFile(
            'img.png',
            _make_png(),
            content_type='image/png',
        )
        form = ServiceForm(
            user=self.user,
            data={
                'title': 'Public Svc',
                'summary': 'A public service',
                'service_type': 'public',
            },
            files={'pdf': pdf, 'image': image},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_public_service_allows_image(self):
        pdf = SimpleUploadedFile(
            'doc.pdf',
            b'PDF',
            content_type='application/pdf',
        )
        image = SimpleUploadedFile(
            'img.png',
            _make_png(),
            content_type='image/png',
        )
        form = ServiceForm(
            user=self.user,
            data={
                'title': 'Public With Image',
                'summary': 'A public service carrying an image',
                'service_type': 'public',
            },
            files={'pdf': pdf, 'image': image},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_public_service_requires_pdf(self):
        image = SimpleUploadedFile(
            'img.png',
            _make_png(),
            content_type='image/png',
        )
        form = ServiceForm(
            user=self.user,
            data={
                'title': 'No PDF',
                'summary': 'Should fail',
                'service_type': 'public',
            },
            files={'image': image},
        )
        self.assertFalse(form.is_valid())
        self.assertIn('pdf', form.errors)

    def test_public_service_requires_image(self):
        pdf = SimpleUploadedFile(
            'doc.pdf',
            b'PDF',
            content_type='application/pdf',
        )
        form = ServiceForm(
            user=self.user,
            data={
                'title': 'No Image',
                'summary': 'Should fail',
                'service_type': 'public',
            },
            files={'pdf': pdf},
        )
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

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
    """La unidad la decide el servicio y la suscripción no vence."""

    INICIO = '15/01/2026'

    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('subform')
        cls.customer = natural_customer(
            cls.user, address='Addr', phone='12345678', account='1234567890123456'
        )
        cls.pronostico = Service.objects.create(
            user=cls.user,
            title='Pronóstico diario',
            summary='Commercial',
            service_type='commercial',
            code='C010',
            price=Decimal('60.00'),
        )
        cls.agrometeo = Service.objects.create(
            user=cls.user,
            title='Boletín agrometeorológico',
            summary='Commercial',
            service_type='commercial',
            code='C011',
            price=Decimal('300.00'),
            service_category='agrometeo',
        )
        cls.publico = Service.objects.create(
            user=cls.user,
            title='Pronóstico público',
            summary='Public',
            service_type='public',
            code='P001',
            price=Decimal('0.00'),
        )

    def _data(self, **overrides):
        data = {
            'customer': self.customer.pk,
            'service': self.pronostico.pk,
            'start_date': self.INICIO,
            'quantity': '45',
            'payment_method': 'qr',
        }
        data.update(overrides)
        return data

    def _rotulo_cantidad(self, service):
        """Etiqueta de la cantidad con el servicio ya elegido (alta de una instancia)."""
        instancia = ServiceSubscription(
            customer=self.customer,
            service=service,
            start_date=timezone.make_aware(datetime(2026, 1, 15)),
            quantity=3,
            payment_status='requested',
            payment_method='qr',
        )
        return SubscriptionForm(instance=instancia).fields['quantity'].label

    def test_los_servicios_se_agrupan_por_categoria(self):
        """La categoría es lo único que define la unidad, así que agrupa la lista."""
        html = SubscriptionForm().fields['service'].widget.render('service', '')
        self.assertIn('<optgroup label="Agrometeorológico">', html)
        self.assertIn('<optgroup label="Pronóstico">', html)
        self.assertNotIn('Pronóstico público', html)

    def test_el_grupo_usa_el_nombre_legible_y_no_la_clave(self):
        form = SubscriptionForm()
        nombres = [str(g[0]) for g in form.fields['service'].widget.optgroups('service', '')]
        self.assertIn('Agrometeorológico', nombres)
        self.assertNotIn('agrometeo', nombres)

    def test_los_campos_del_formulario(self):
        form = SubscriptionForm()
        self.assertEqual(
            list(form.fields),
            ['customer', 'service', 'start_date', 'quantity', 'payment_method'],
        )

    def test_period_ya_no_es_un_campo(self):
        self.assertNotIn('period', SubscriptionForm().fields)

    def test_end_date_no_es_editable(self):
        self.assertNotIn('end_date', SubscriptionForm().fields)

    def test_end_date_enviado_en_el_post_se_ignora(self):
        form = SubscriptionForm(data=self._data(end_date='01/01/2030'))
        self.assertTrue(form.is_valid(), form.errors)
        sub = form.save(commit=False)
        self.assertFalse(hasattr(sub, 'end_date'))

    def test_cantidad_es_obligatoria(self):
        form = SubscriptionForm(data=self._data(quantity=''))
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)

    def test_cantidad_rechaza_el_cero(self):
        form = SubscriptionForm(data=self._data(quantity='0'))
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)

    def test_cantidad_exige_el_minimo_del_modelo(self):
        form = SubscriptionForm()
        field = form.fields['quantity']
        self.assertTrue(field.required)
        self.assertEqual(field.min_value, 1)
        self.assertIn('min="1"', form['quantity'].as_widget())

    def test_start_date_es_obligatorio(self):
        form = SubscriptionForm(data=self._data(start_date=''))
        self.assertFalse(form.is_valid())
        self.assertIn('start_date', form.errors)

    def test_start_date_pasado_se_acepta(self):
        # El inicio es libre, incluso en el pasado: la fecha es un dato del
        # acuerdo con el cliente, no un valor que se rellene con el momento actual.
        form = SubscriptionForm(data=self._data(start_date='01/09/2025'))
        self.assertTrue(form.is_valid(), form.errors)
        sub = form.save(commit=False)
        self.assertEqual(sub.start_date.strftime('%d/%m/%Y'), '01/09/2025')

    def test_start_date_acepta_el_formato_iso(self):
        # El mismo campo llega en los dos formatos: el del navegador y el de
        # Tempus. Aceptar sólo uno rompe la captura según de dónde venga el dato.
        form = SubscriptionForm(data=self._data(start_date='2026-01-15'))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['start_date'], date(2026, 1, 15))

    def test_start_date_es_solo_fecha(self):
        """La fecha de inicio no lleva hora: el servicio empieza ese día.

        Antes el campo aceptaba `15/01/2026 08:00 AM` porque el vencimiento se
        derivaba por aritmética de meses y días. Sin vencimiento la hora no
        significa nada, y aceptarla dejaba en el modelo una precisión que la
        pantalla nunca pidió. Ahora sólo `%d/%m/%Y`.
        """
        form = SubscriptionForm(data=self._data(start_date='15/01/2026 08:00 AM'))
        self.assertFalse(form.is_valid())
        self.assertIn('start_date', form.errors)

    def test_start_date_se_rotula_y_se_ayuda_como_en_home(self):
        field = SubscriptionForm().fields['start_date']
        self.assertEqual(field.label, 'Fecha de inicio del servicio')
        self.assertEqual(field.help_text, 'Fecha desde la cual necesita el servicio.')

    def test_las_opciones_de_servicio_exponen_la_unidad(self):
        opciones = SubscriptionForm()['service'].as_widget()
        self.assertIn(f'value="{self.agrometeo.pk}" data-period-unit="mes"', opciones)
        self.assertIn(f'value="{self.pronostico.pk}" data-period-unit="día"', opciones)

    def test_el_rotulo_de_cantidad_usa_la_unidad_del_servicio(self):
        self.assertEqual(self._rotulo_cantidad(self.agrometeo), 'Cantidad de meses')
        self.assertEqual(self._rotulo_cantidad(self.pronostico), 'Cantidad de días')

    def test_el_rotulo_de_cantidad_es_neutro_sin_servicio(self):
        campo = SubscriptionForm().fields['quantity']
        self.assertEqual(campo.label, 'Cantidad')
        self.assertEqual(
            campo.help_text,
            'El importe total se calcula multiplicando el precio por la cantidad seleccionada.',
        )

    def test_el_rotulo_de_cantidad_tras_un_post_invalido_usa_el_servicio_enviado(self):
        form = SubscriptionForm(data=self._data(service=self.agrometeo.pk, quantity=''))
        self.assertEqual(form.fields['quantity'].label, 'Cantidad de meses')

    def test_el_rotulo_de_cantidad_no_falla_con_un_servicio_inventado(self):
        form = SubscriptionForm(data=self._data(service=self.publico.pk, quantity=''))
        self.assertEqual(form.fields['quantity'].label, 'Cantidad')
        form = SubscriptionForm(data=self._data(service='no-existe', quantity=''))
        self.assertEqual(form.fields['quantity'].label, 'Cantidad')

    def test_el_servicio_publico_no_se_ofrece(self):
        disponibles = SubscriptionForm().fields['service'].queryset
        self.assertIn(self.pronostico, disponibles)
        self.assertIn(self.agrometeo, disponibles)
        self.assertNotIn(self.publico, disponibles)

    def test_el_estado_de_pago_no_es_un_campo_del_formulario(self):
        instancia = ServiceSubscription.objects.create(
            customer=self.customer,
            service=self.pronostico,
            start_date=timezone.make_aware(datetime(2026, 1, 15)),
            quantity=45,
            payment_status='paid',
            payment_method='qr',
        )
        self.assertNotIn('payment_status', SubscriptionForm().fields)
        form = SubscriptionForm(data=self._data(), instance=instancia)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save(commit=False).payment_status, 'paid')

    def test_el_metodo_de_pago_es_obligatorio(self):
        form = SubscriptionForm(data=self._data(payment_method=''))
        self.assertFalse(form.is_valid())
        self.assertIn('payment_method', form.errors)

    def test_el_metodo_de_pago_sale_de_las_choices_del_modelo(self):
        self.assertEqual(
            SubscriptionForm().fields['payment_method'].choices,
            ServiceSubscription.PAYMENT_METHOD_CHOICES,
        )

    def test_el_metodo_de_pago_rechaza_un_valor_inexistente(self):
        form = SubscriptionForm(data=self._data(payment_method='cripto'))
        self.assertFalse(form.is_valid())
        self.assertIn('payment_method', form.errors)

    def test_el_metodo_de_pago_se_guarda(self):
        form = SubscriptionForm(data=self._data(payment_method='transfer'))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save(commit=False).payment_method, 'transfer')

    def test_el_formulario_no_expone_el_vencimiento_calculado(self):
        self.assertFalse(hasattr(SubscriptionForm(), 'derived_end_date'))

    def test_el_formulario_no_tiene_ningun_campo_de_vencimiento(self):
        for nombre in SubscriptionForm().fields:
            self.assertNotIn('end', nombre)
            self.assertNotIn('expir', nombre)


class ContractFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('conform')
        customer = natural_customer(
            cls.user, address='Addr', phone='12345678', account='1234567890123456'
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
        customer = natural_customer(
            cls.user, address='Addr', phone='12345678', account='1234567890123456'
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
                'quantity': 1,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_requires_quantity(self):
        form = PaymentMethodForm(data={'payment_method': 'transfer'})
        self.assertFalse(form.is_valid())
        self.assertIn('start_date', form.errors)
        self.assertIn('quantity', form.errors)

    def test_quantity_min_one(self):
        form = PaymentMethodForm(
            data={
                'payment_method': 'qr',
                'start_date': date.today().isoformat(),
                'quantity': 0,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)

    def test_has_no_end_date_field(self):
        form = PaymentMethodForm(data={})
        self.assertNotIn('end_date', form.fields)
        self.assertIn('quantity', form.fields)

    def test_quantity_label_by_billing_period_dia(self):
        form = PaymentMethodForm(billing_period='día')
        self.assertIn('días', form.fields['quantity'].label)

    def test_quantity_label_by_billing_period_mes(self):
        form = PaymentMethodForm(billing_period='mes')
        self.assertIn('meses', form.fields['quantity'].label)

    def test_quantity_help_text_does_not_hardcode_categories(self):
        form = PaymentMethodForm(billing_period='día')
        help_text = form.fields['quantity'].help_text
        self.assertNotIn('agrometeo', help_text)
        self.assertNotIn('pronóstico', help_text)
        # El texto no repite "Cantidad de períodos" (confunde): explica cómo se
        # calcula el importe sin encajar categorías hardcodeadas.
        self.assertIn('multiplicando el precio', help_text)


class InvoiceFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('invform')
        cls.customer = natural_customer(
            cls.user, address='Addr', phone='12345678', account='1234567890123456'
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


class InvoiceItemFormTests(TestCase):
    """B4: la línea manual deriva unidad y precio del servicio, no del POST."""

    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('itemform')
        cls.agro = Service.objects.create(
            user=cls.user,
            title='Agrometeo',
            summary='S',
            service_type=Service.COMMERCIAL,
            service_category='agrometeo',
            code='AGRO-01',
            price=Decimal('120.00'),
        )
        cls.pronostico = Service.objects.create(
            user=cls.user,
            title='Pronóstico',
            summary='S',
            service_type=Service.COMMERCIAL,
            service_category='pronostico',
            code='PRO-01',
            price=Decimal('5.00'),
        )

    def _data(self, service, **overrides):
        # El navegador manda el precio del servicio; clean() lo vuelve a derivar igual.
        data = {
            'service': service.pk,
            'codigo': service.code or '',
            'cantidad': 3,
            'unidad_medida': 'U',
            'precio': f'{service.price:.2f}',
        }
        data.update(overrides)
        return data

    def test_clean_overrides_posted_derived_fields(self):
        """Invariante de seguridad: el POST no puede fijar código, precio ni UM."""
        form = InvoiceItemForm(
            data=self._data(
                self.pronostico,
                codigo='HACKED',
                unidad_medida='MES',
                precio='9999.99',
            )
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['codigo'], 'PRO-01')
        self.assertEqual(form.cleaned_data['precio'], Decimal('5.00'))
        self.assertEqual(form.cleaned_data['unidad_medida'], 'DÍA')

    def test_agrometeo_unit_is_mes(self):
        form = InvoiceItemForm(data=self._data(self.agro))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['unidad_medida'], 'MES')

    def test_pronostico_unit_is_dia(self):
        form = InvoiceItemForm(data=self._data(self.pronostico))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['unidad_medida'], 'DÍA')

    def test_cantidad_comes_from_the_operator(self):
        """La cantidad es del operador: clean() no la toca, la plantilla sólo propone."""
        form = InvoiceItemForm(data=self._data(self.agro, cantidad=7))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['cantidad'], 7)

    def test_missing_cantidad_is_a_validation_error(self):
        data = self._data(self.agro)
        del data['cantidad']
        form = InvoiceItemForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('cantidad', form.errors)

    def test_empty_cantidad_is_a_validation_error(self):
        form = InvoiceItemForm(data=self._data(self.agro, cantidad=''))
        self.assertFalse(form.is_valid())
        self.assertIn('cantidad', form.errors)

    def test_cantidad_below_minimum_is_rejected(self):
        form = InvoiceItemForm(data=self._data(self.agro, cantidad=0))
        self.assertFalse(form.is_valid())
        self.assertIn('cantidad', form.errors)

    def test_service_without_code_falls_back_to_empty_codigo(self):
        service = Service.objects.create(
            user=self.user,
            title='Sin código',
            summary='S',
            service_type=Service.COMMERCIAL,
            service_category='pronostico',
            price=Decimal('10.00'),
        )
        form = InvoiceItemForm(data=self._data(service, codigo='HACKED'))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['codigo'], '')
