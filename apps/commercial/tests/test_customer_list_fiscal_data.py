"""El listado de clientes unifica identidad en una sola columna.

Para persona natural se muestra el documento de identidad. Para persona
jurídica se muestran REEUP y NIT con sus etiquetas. El guion largo solo
aparece como último recurso cuando falta el dato que debería estar.
"""

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from apps.commercial.models import Customer
from apps.commercial.tests.factories import make_user


class CustomerListFiscalDataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from apps.core.models import SiteConfiguration

        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        cls.staff_user = User.objects.create_user(
            'staff.fiscal', 'staff.fiscal@example.com', 'pass', first_name='Sta', last_name='F'
        )
        ct = ContentType.objects.get_for_model(Customer)
        cls.staff_user.user_permissions.add(ct.permission_set.get(codename='view_customer'))
        cls.url = reverse('commercial:cliente_list')

    def _html(self):
        self.client.force_login(self.staff_user)
        return self.client.get(self.url).content.decode()

    def test_juridica_muestra_reeup_y_nit_en_columna_unificada(self):
        Customer.objects.create(
            client_type='juridica',
            user=make_user('juridica.con.fiscal', first_name='Empresa', last_name='S.A.'),
            company_name='Empresa Con Fiscal S.A.',
            reeup='123.4.5678',
            nit='98765432101',
            account='1234567890123456',
            address='Calle 1',
            phone='71234567',
        )
        html = self._html()
        self.assertIn('REEUP', html)
        self.assertIn('123.4.5678', html)
        self.assertIn('NIT', html)
        self.assertIn('98765432101', html)

    def test_natural_muestra_carnet_sin_etiquetas_fiscales(self):
        Customer.objects.create(
            client_type='natural',
            user=make_user('natural.lista', first_name='Ana', last_name='Norte'),
            identity_document='34111234567',
            account='1234567890123456',
            address='Calle 1',
            phone='71234567',
        )
        html = self._html()
        self.assertIn('34111234567', html)
        self.assertNotIn('REEUP', html)
        self.assertNotIn('NIT', html)
